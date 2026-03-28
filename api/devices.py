# -*- coding: utf-8 -*-
"""
设备API
处理设备管理和分组管理
"""

from flask import Blueprint, request, jsonify
from datetime import datetime
from models.user import db
from models.device import Device, DeviceGroup
from utils.auth import login_required, log_operation
from flask_login import current_user

devices_bp = Blueprint('devices', __name__, url_prefix='/api/v1/devices')


@devices_bp.route('/groups', methods=['GET'])
@login_required
def get_groups():
    """获取设备分组列表"""
    groups = DeviceGroup.query.order_by(DeviceGroup.name).all()
    return jsonify({
        'code': 200,
        'message': 'success',
        'data': [g.to_dict() for g in groups]
    })


@devices_bp.route('/groups', methods=['POST'])
@login_required
def create_group():
    """创建设备分组"""
    data = request.get_json()
    name = data.get('name', '').strip()

    if not name:
        return jsonify({'code': 400, 'message': '分组名称不能为空', 'data': None})

    group = DeviceGroup(
        name=name,
        parent_id=data.get('parent_id'),
        description=data.get('description')
    )

    db.session.add(group)
    db.session.commit()

    log_operation(current_user.id, 'create_device_group', f'创建设备分组: {name}')

    return jsonify({
        'code': 200,
        'message': '创建成功',
        'data': group.to_dict()
    })


@devices_bp.route('/groups/<int:group_id>', methods=['PUT'])
@login_required
def update_group(group_id):
    """更新设备分组"""
    group = DeviceGroup.query.get(group_id)
    if not group:
        return jsonify({'code': 404, 'message': '分组不存在', 'data': None})

    data = request.get_json()
    if 'name' in data:
        group.name = data['name']
    if 'parent_id' in data:
        group.parent_id = data['parent_id']
    if 'description' in data:
        group.description = data['description']

    db.session.commit()

    log_operation(current_user.id, 'update_device_group', f'更新设备分组: {group.name}')

    return jsonify({
        'code': 200,
        'message': '更新成功',
        'data': group.to_dict()
    })


@devices_bp.route('/groups/<int:group_id>', methods=['DELETE'])
@login_required
def delete_group(group_id):
    """删除设备分组"""
    group = DeviceGroup.query.get(group_id)
    if not group:
        return jsonify({'code': 404, 'message': '分组不存在', 'data': None})

    # 检查是否有子分组
    if group.children:
        return jsonify({'code': 400, 'message': '该分组下有子分组，无法删除', 'data': None})

    # 检查是否有设备
    if group.devices.count() > 0:
        return jsonify({'code': 400, 'message': '该分组下有设备，无法删除', 'data': None})

    db.session.delete(group)
    db.session.commit()

    log_operation(current_user.id, 'delete_device_group', f'删除设备分组: {group.name}')

    return jsonify({'code': 200, 'message': '删除成功', 'data': None})


@devices_bp.route('', methods=['GET'])
@login_required
def get_devices():
    """获取设备列表"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    group_id = request.args.get('group_id', type=int)
    status = request.args.get('status', type=int)
    keyword = request.args.get('keyword', '').strip()

    query = Device.query

    if group_id is not None:
        query = query.filter_by(group_id=group_id)
    if status is not None:
        query = query.filter_by(status=status)
    if keyword:
        query = query.filter(Device.name.contains(keyword))

    pagination = query.order_by(Device.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )

    return jsonify({
        'code': 200,
        'message': 'success',
        'data': {
            'items': [d.to_dict() for d in pagination.items],
            'total': pagination.total,
            'pages': pagination.pages,
            'current_page': page,
            'per_page': per_page
        }
    })


@devices_bp.route('', methods=['POST'])
@login_required
def create_device():
    """创建设备"""
    data = request.get_json()
    name = data.get('name', '').strip()

    if not name:
        return jsonify({'code': 400, 'message': '设备名称不能为空', 'data': None})

    device = Device(
        name=name,
        device_type=data.get('device_type', 'camera'),
        protocol=data.get('protocol'),
        address=data.get('address'),
        group_id=data.get('group_id'),
        location=data.get('location'),
        latitude=data.get('latitude'),
        longitude=data.get('longitude'),
        config=data.get('config')
    )

    db.session.add(device)
    db.session.commit()

    log_operation(current_user.id, 'create_device', f'创建设备: {name}')

    return jsonify({
        'code': 200,
        'message': '创建成功',
        'data': device.to_dict()
    })


@devices_bp.route('/<int:device_id>', methods=['GET'])
@login_required
def get_device(device_id):
    """获取设备详情"""
    device = Device.query.get(device_id)
    if not device:
        return jsonify({'code': 404, 'message': '设备不存在', 'data': None})

    return jsonify({
        'code': 200,
        'message': 'success',
        'data': device.to_dict()
    })


@devices_bp.route('/<int:device_id>', methods=['PUT'])
@login_required
def update_device(device_id):
    """更新设备"""
    device = Device.query.get(device_id)
    if not device:
        return jsonify({'code': 404, 'message': '设备不存在', 'data': None})

    data = request.get_json()

    if 'name' in data:
        device.name = data['name']
    if 'device_type' in data:
        device.device_type = data['device_type']
    if 'protocol' in data:
        device.protocol = data['protocol']
    if 'address' in data:
        device.address = data['address']
    if 'group_id' in data:
        device.group_id = data['group_id']
    if 'location' in data:
        device.location = data['location']
    if 'latitude' in data:
        device.latitude = data['latitude']
    if 'longitude' in data:
        device.longitude = data['longitude']
    if 'status' in data:
        device.status = data['status']
    if 'config' in data:
        device.config = data['config']

    db.session.commit()

    log_operation(current_user.id, 'update_device', f'更新设备: {device.name}')

    return jsonify({
        'code': 200,
        'message': '更新成功',
        'data': device.to_dict()
    })


@devices_bp.route('/<int:device_id>', methods=['DELETE'])
@login_required
def delete_device(device_id):
    """删除设备"""
    device = Device.query.get(device_id)
    if not device:
        return jsonify({'code': 404, 'message': '设备不存在', 'data': None})

    db.session.delete(device)
    db.session.commit()

    log_operation(current_user.id, 'delete_device', f'删除设备: {device.name}')

    return jsonify({'code': 200, 'message': '删除成功', 'data': None})


@devices_bp.route('/<int:device_id>/status', methods=['PUT'])
@login_required
def update_device_status(device_id):
    """更新设备状态"""
    device = Device.query.get(device_id)
    if not device:
        return jsonify({'code': 404, 'message': '设备不存在', 'data': None})

    data = request.get_json()
    device.status = data.get('status', 0)
    db.session.commit()

    return jsonify({
        'code': 200,
        'message': '状态更新成功',
        'data': device.to_dict()
    })

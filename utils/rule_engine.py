# -*- coding: utf-8 -*-
"""
规则引擎
用于评估检测结果是否触发告警规则
"""

from datetime import datetime, timedelta
import json


class RuleEngine:
    """规则引擎类"""

    def __init__(self):
        """初始化规则引擎"""
        self.rule_handlers = {
            'count': self._evaluate_count_rule,
            'exists': self._evaluate_exists_rule,
            'area': self._evaluate_area_rule,
            'combination': self._evaluate_combination_rule,
            'trend': self._evaluate_trend_rule
        }

    def evaluate_rule(self, rule, detections, context=None):
        """
        评估单条规则

        Args:
            rule: 告警规则对象
            detections: 检测结果列表
            context: 上下文信息（设备ID、场景ID等）

        Returns:
            dict: 评估结果 {'triggered': bool, 'message': str, 'details': dict}
        """
        if not rule.is_enabled:
            return {'triggered': False, 'message': '规则未启用', 'details': {}}

        handler = self.rule_handlers.get(rule.rule_type)
        if not handler:
            return {'triggered': False, 'message': f'未知规则类型: {rule.rule_type}', 'details': {}}

        try:
            return handler(rule, detections, context)
        except Exception as e:
            return {'triggered': False, 'message': f'规则评估错误: {str(e)}', 'details': {}}

    def evaluate_rules(self, rules, detections, context=None):
        """
        批量评估规则

        Args:
            rules: 告警规则列表
            detections: 检测结果列表
            context: 上下文信息

        Returns:
            list: 触发的规则列表
        """
        triggered_rules = []

        for rule in rules:
            result = self.evaluate_rule(rule, detections, context)
            if result['triggered']:
                triggered_rules.append({
                    'rule': rule,
                    'result': result
                })

        return triggered_rules

    def _evaluate_count_rule(self, rule, detections, context):
        """
        数量规则评估
        条件格式: {"class_name": "person", "operator": "gt", "value": 5}
        """
        conditions = rule.conditions
        if not conditions:
            return {'triggered': False, 'message': '缺少条件配置', 'details': {}}

        class_name = conditions.get('class_name', '')
        operator = conditions.get('operator', 'gt')
        value = conditions.get('value', 0)

        # 统计目标数量
        count = sum(1 for d in detections if d.get('class_name') == class_name)

        # 比较
        triggered = False
        if operator == 'gt':
            triggered = count > value
        elif operator == 'gte':
            triggered = count >= value
        elif operator == 'lt':
            triggered = count < value
        elif operator == 'lte':
            triggered = count <= value
        elif operator == 'eq':
            triggered = count == value
        elif operator == 'ne':
            triggered = count != value

        message = f'检测到{class_name}数量: {count}，阈值: {value}' if triggered else ''

        return {
            'triggered': triggered,
            'message': message,
            'details': {
                'class_name': class_name,
                'count': count,
                'threshold': value,
                'operator': operator
            }
        }

    def _evaluate_exists_rule(self, rule, detections, context):
        """
        存在规则评估
        条件格式: {"class_names": ["person", "car"], "mode": "any"}
        """
        conditions = rule.conditions
        if not conditions:
            return {'triggered': False, 'message': '缺少条件配置', 'details': {}}

        class_names = conditions.get('class_names', [])
        mode = conditions.get('mode', 'any')  # any/all

        detected_classes = set(d.get('class_name') for d in detections)

        if mode == 'any':
            triggered = any(cn in detected_classes for cn in class_names)
            matched = [cn for cn in class_names if cn in detected_classes]
        else:  # all
            triggered = all(cn in detected_classes for cn in class_names)
            matched = class_names if triggered else []

        message = f'检测到目标: {", ".join(matched)}' if triggered else ''

        return {
            'triggered': triggered,
            'message': message,
            'details': {
                'class_names': class_names,
                'mode': mode,
                'matched': matched
            }
        }

    def _evaluate_area_rule(self, rule, detections, context):
        """
        区域规则评估
        条件格式: {"area": {"x": 0, "y": 0, "w": 100, "h": 100}, "class_name": "person"}
        """
        conditions = rule.conditions
        if not conditions:
            return {'triggered': False, 'message': '缺少条件配置', 'details': {}}

        area = conditions.get('area', {})
        class_name = conditions.get('class_name', '')

        ax, ay, aw, ah = area.get('x', 0), area.get('y', 0), area.get('w', 0), area.get('h', 0)

        # 检查是否有目标在指定区域内
        in_area_detections = []
        for det in detections:
            if class_name and det.get('class_name') != class_name:
                continue

            bbox = det.get('bbox', {})
            bx, by, bw, bh = bbox.get('x', 0), bbox.get('y', 0), bbox.get('w', 0), bbox.get('h', 0)

            # 检查目标中心点是否在区域内
            center_x = bx + bw / 2
            center_y = by + bh / 2

            if ax <= center_x <= ax + aw and ay <= center_y <= ay + ah:
                in_area_detections.append(det)

        triggered = len(in_area_detections) > 0
        message = f'区域内检测到{len(in_area_detections)}个目标' if triggered else ''

        return {
            'triggered': triggered,
            'message': message,
            'details': {
                'area': area,
                'class_name': class_name,
                'count': len(in_area_detections)
            }
        }

    def _evaluate_combination_rule(self, rule, detections, context):
        """
        组合规则评估
        条件格式: {"rules": [...], "mode": "and/or"}
        """
        conditions = rule.conditions
        if not conditions:
            return {'triggered': False, 'message': '缺少条件配置', 'details': {}}

        sub_rules = conditions.get('rules', [])
        mode = conditions.get('mode', 'and')

        results = []
        for sub_rule_config in sub_rules:
            # 创建临时规则对象进行评估
            from types import SimpleNamespace
            sub_rule = SimpleNamespace(
                rule_type=sub_rule_config.get('type', 'count'),
                conditions=sub_rule_config.get('conditions', {}),
                is_enabled=True
            )
            result = self.evaluate_rule(sub_rule, detections, context)
            results.append(result['triggered'])

        if mode == 'and':
            triggered = all(results)
        else:  # or
            triggered = any(results)

        message = f'组合规则{"触发" if triggered else "未触发"}' if triggered else ''

        return {
            'triggered': triggered,
            'message': message,
            'details': {
                'mode': mode,
                'sub_results': results
            }
        }

    def _evaluate_trend_rule(self, rule, detections, context):
        """
        趋势规则评估
        条件格式: {"class_name": "person", "window_minutes": 5, "threshold_percent": 50}
        """
        conditions = rule.conditions
        if not conditions:
            return {'triggered': False, 'message': '缺少条件配置', 'details': {}}

        # 趋势规则需要历史数据，这里只返回基本逻辑
        # 实际应用中需要从数据库查询历史统计数据

        return {
            'triggered': False,
            'message': '趋势规则需要历史数据支持',
            'details': {}
        }

    def test_rule(self, rule_config, test_detections):
        """
        测试规则

        Args:
            rule_config: 规则配置
            test_detections: 测试用的检测结果

        Returns:
            dict: 测试结果
        """
        from types import SimpleNamespace

        rule = SimpleNamespace(
            rule_type=rule_config.get('rule_type', 'count'),
            conditions=rule_config.get('conditions', {}),
            is_enabled=True
        )

        return self.evaluate_rule(rule, test_detections)

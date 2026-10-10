from app.collectors.nbs import month_range


def build_series(rows, start, end, metric):
    """对齐月份，缺失不填零；累计相对指数在断档后停止，避免虚构连续走势。"""
    lookup = {row.period: row for row in rows}
    points, level, broken = [], None, False
    for period in month_range(start, end):
        row = lookup.get(period)
        value = None
        if metric == 'relative_index':
            if period == start:
                level = 100.0 if row else None
                broken = row is None
            elif not broken:
                if not row or row.mom_index is None:
                    broken = True
                else:
                    level *= row.mom_index / 100
            if row and not broken:
                value = round(level, 4)
        elif row:
            index = row.mom_index if metric == 'mom_change' else row.yoy_index
            value = round(index - 100, 4) if index is not None else None
        points.append({'period': period, 'value': value, 'source_id': row.source_id if row else None})
    return points

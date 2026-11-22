# -*- coding: utf-8 -*-
# CBR(象棋桥)棋盘/规则模型
# 行0=黑底(上), 行9=红底(下); 列0-8 从左到右; 坐标编码 = 行*9 + 列
# 棋码: 红方 11-17(车马相仕帅炮兵), 黑方 21-27(車馬象士将砲卒)
# 红方行号递减为进, 黑方行号递增为进

RED_CH = {1: '俥', 2: '馬', 3: '相', 4: '仕', 5: '帥', 6: '炮', 7: '兵'}
BLK_CH = {1: '車', 2: '马', 3: '象', 4: '士', 5: '将', 6: '砲', 7: '卒'}
RED_NUM = '一二三四五六七八九'
BLK_NUM = '123456789'


def initial_board():
    b = [[0] * 9 for _ in range(10)]
    back = [1, 2, 3, 4, 5, 4, 3, 2, 1]
    for c in range(9):
        b[0][c] = 20 + back[c]
        b[9][c] = 10 + back[c]
    b[2][1] = 26; b[2][7] = 26
    b[7][1] = 16; b[7][7] = 16
    for c in (0, 2, 4, 6, 8):
        b[3][c] = 27
        b[6][c] = 17
    return b


def side_of(code):
    return 'r' if code < 20 else 'b'


def kind(code):
    return code % 10


def inb(r, c):
    return 0 <= r < 10 and 0 <= c < 9


def _kings_facing(board):
    kr = kb = None
    for r in range(10):
        for c in range(9):
            if board[r][c] == 15:
                kr = (r, c)
            elif board[r][c] == 25:
                kb = (r, c)
    if kr is None or kb is None or kr[1] != kb[1]:
        return False
    lo, hi = min(kr[0], kb[0]), max(kr[0], kb[0])
    return all(board[r][kr[1]] == 0 for r in range(lo + 1, hi))


def legal_move(board, frm, to):
    fr, fc = divmod(frm, 9)
    tr, tc = divmod(to, 9)
    if not inb(fr, fc) or not inb(tr, tc) or (fr, fc) == (tr, tc):
        return False
    p = board[fr][fc]
    if not p:
        return False
    tgt = board[tr][tc]
    if tgt and side_of(tgt) == side_of(p):
        return False
    k = kind(p)
    s = side_of(p)
    dr, dc = tr - fr, tc - fc

    if k == 1:  # 车
        if fr != tr and fc != tc:
            return False
        step = 1 if (tr > fr or tc > fc) else -1
        if fr == tr:
            rng = range(min(fc, tc) + 1, max(fc, tc))
            cells = [(fr, c) for c in rng]
        else:
            rng = range(min(fr, tr) + 1, max(fr, tr))
            cells = [(r, fc) for r in rng]
        return all(board[r][c] == 0 for r, c in cells)

    if k == 2:  # 马
        if (abs(dr), abs(dc)) not in ((1, 2), (2, 1)):
            return False
        if abs(dr) == 2:
            return board[fr + dr // 2][fc] == 0
        return board[fr][fc + dc // 2] == 0

    if k == 3:  # 相
        if abs(dr) != 2 or abs(dc) != 2:
            return False
        if s == 'r' and tr < 5:
            return False
        if s == 'b' and tr > 4:
            return False
        return board[fr + dr // 2][fc + dc // 2] == 0

    if k == 4:  # 仕
        if abs(dr) != 1 or abs(dc) != 1:
            return False
        if not (3 <= tc <= 5):
            return False
        if s == 'r':
            return tr >= 7
        return tr <= 2

    if k == 5:  # 帅/将
        if abs(dr) + abs(dc) != 1:
            return False
        if not (3 <= tc <= 5):
            return False
        if s == 'r':
            if tr < 7:
                return False
        else:
            if tr > 2:
                return False
        return True

    if k == 6:  # 炮
        if fr != tr and fc != tc:
            return False
        if fr == tr:
            cells = [(fr, c) for c in range(min(fc, tc) + 1, max(fc, tc))]
        else:
            cells = [(r, fc) for r in range(min(fr, tr) + 1, max(fr, tr))]
        screens = sum(1 for r, c in cells if board[r][c])
        if tgt == 0:
            return screens == 0
        return screens == 1

    if k == 7:  # 兵/卒
        if s == 'r':
            fwd = dr == -1 and dc == 0
            side = dr == 0 and abs(dc) == 1 and fr <= 4
        else:
            fwd = dr == 1 and dc == 0
            side = dr == 0 and abs(dc) == 1 and fr >= 5
        return fwd or side

    return False


def legal_moves(board, side):
    out = []
    for r in range(10):
        for c in range(9):
            p = board[r][c]
            if p and side_of(p) == side:
                for tr in range(10):
                    for tc in range(9):
                        if legal_move(board, r * 9 + c, tr * 9 + tc):
                            # 走完后双王不得照面
                            nb = [row[:] for row in board]
                            nb[tr][tc] = nb[r][c]
                            nb[r][c] = 0
                            if _kings_facing(nb):
                                continue
                            out.append((r * 9 + c, tr * 9 + tc))
    return out


def play(board, mv):
    frm, to = mv
    fr, fc = divmod(frm, 9)
    tr, tc = divmod(to, 9)
    board[tr][tc] = board[fr][fc]
    board[fr][fc] = 0


def move_text(board, frm, to):
    """走子前的局面下, 生成与棋谱 txt 一致的标准记谱"""
    fr, fc = divmod(frm, 9)
    tr, tc = divmod(to, 9)
    p = board[fr][fc]
    s = side_of(p)
    k = kind(p)
    ch = RED_CH[k] if s == 'r' else BLK_CH[k]
    num = RED_NUM if s == 'r' else BLK_NUM

    def ffile(c):
        return num[8 - c] if s == 'r' else str(c + 1)

    # 同列存在同种同方棋子时用 前/后 消歧(红/黑: 越靠前线越"前")
    others = [r for r in range(10) if r != fr and board[r][fc] == p]
    if others:
        if s == 'r':
            head = ('前' if fr < max(others) else '后') + ch
        else:
            head = ('前' if fr > min(others) else '后') + ch
    else:
        head = ch + ffile(fc)

    if tr == fr:
        act = '平' + ffile(tc)
    else:
        fwd = (tr < fr) if s == 'r' else (tr > fr)
        d = '进' if fwd else '退'
        if k in (1, 5, 6, 7):  # 车/帅/炮/兵: 进退按行数
            n = num[abs(tr - fr) - 1]
        else:                  # 马/相/仕: 按目标线
            n = ffile(tc)
        act = d + n
    return head + act

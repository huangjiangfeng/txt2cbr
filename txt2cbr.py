# -*- coding: utf-8 -*-
# 用法: python txt2cbr.py <输入.txt> <输出.cbr> [模板.cbr]
# 模板也可通过环境变量 CBR_TEMPLATE 指定; 省略时按内置默认路径查找。
# 逐着穷举合法着法, 用标准记谱法反写字符串与原文精确比对, 唯一命中才采用
import os
import sys
from cbr_model import (initial_board, legal_moves, play, move_text,
                       side_of, kind, RED_CH, BLK_CH)

# 象棋桥(CCBridge)空棋谱模板路径: 可用第3个参数或 CBR_TEMPLATE 覆盖
DEFAULT_TPL = r'C:\D\GREENSOFT\CCBridge3\1102.cbr'
SIG = bytes([0x21, 0x22, 0x23, 0x24, 0x25, 0x24, 0x23, 0x22, 0x21])
# 着法区偏移 = 棋盘签名位置 + 0x64


def find_move(board, side, txt):
    hits = [mv for mv in legal_moves(board, side)
            if move_text(board, mv[0], mv[1]) == txt]
    if len(hits) == 1:
        return hits[0]
    if not hits:
        return None
    raise SystemExit(f'着法歧义(命中{len(hits)}处): {txt}')


def convert(txt_path, cbr_path, tpl_path):
    raw = open(txt_path, 'rb').read()
    for enc in ('utf-8', 'gbk'):
        try:
            text = raw.decode(enc)
            break
        except UnicodeDecodeError:
            continue

    lines = [l.strip() for l in text.splitlines() if l.strip()]

    board = initial_board()
    moves = []
    side = 'r'
    for ln in lines:
        for txt in (p.strip() for p in ln.split(',')):
            if not txt:
                continue
            mv = find_move(board, side, txt)
            if mv is None:
                cand = sorted({move_text(board, a, b)
                               for a, b in legal_moves(board, side)})
                raise SystemExit(f'无法匹配着法: 「{txt}」 (行: {ln})\n该方可走: {cand}')
            moves.append(mv)
            play(board, mv)
            side = 'b' if side == 'r' else 'r'

    tpl = open(tpl_path, 'rb').read()
    sig_off = tpl.find(SIG)
    if sig_off < 0:
        raise SystemExit('模板中未找到棋盘签名, 请确认是正确的 CBR 空棋谱模板')
    area_off = sig_off + 0x64
    out = bytearray(tpl[:area_off])
    n = len(moves)
    for i, (frm, to) in enumerate(moves):
        if i == n - 1:          # 末条只写 2 字节
            out += bytes([frm, to])
        elif i == n - 2:        # 倒数第二条标志 0x01
            out += bytes([frm, to, 1, 0])
        else:
            out += bytes([frm, to, 0, 0])
    open(cbr_path, 'wb').write(bytes(out))
    return n


if __name__ == '__main__':
    if len(sys.argv) not in (3, 4):
        raise SystemExit('用法: python txt2cbr.py <输入.txt> <输出.cbr> [模板.cbr]')
    src, dst = sys.argv[1], sys.argv[2]
    tpl_path = (sys.argv[3] if len(sys.argv) == 4
                else os.environ.get('CBR_TEMPLATE', DEFAULT_TPL))
    n = convert(src, dst, tpl_path)
    print(f'OK: {dst} 共 {n} 着, 文件 {len(open(dst,"rb").read())} 字节')

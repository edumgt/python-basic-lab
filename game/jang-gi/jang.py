#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
한국 장기(將棋) 게임 - pygame 구현 (규칙 반영 버전)

- 보드: 9 x 10 (x: 0~8, y: 0~9)  → board[y][x]
- 초(紅, 아래) / 한(藍, 위) 기본 배치
- 말 움직임 (단순화/근사 포함):
  - 차(車): 직선 무제한
  - 포(包): 직선, 반드시 1개의 스크린(중간말)을 넘어 상대 말만 잡기
           포는 포를 넘을 수 없고, 포를 잡을 수 없음
  - 마(馬): 1칸 직진 + 1칸 대각, 발 막힘 반영
  - 상(象): 대각 2칸 (발 막힘은 간단 버전 – 필요시 세부 구현 가능)
  - 사(士) & 장/수(將/帥): 궁 내에서 상하좌우+대각 한 칸
  - 졸/병(卒/兵): 전·좌·우 1칸, 강을 건넌 뒤에는 후진도 1칸 가능
- 체크/체크메이트 + 장수 마주보기(직선 상 왕끼리 사이 비어 있으면 체크)
"""

import pygame
import sys

# ------------------------------------------------------------
# 상수 정의
# ------------------------------------------------------------
BOARD_WIDTH, BOARD_HEIGHT = 9, 10      # x: 0~8, y: 0~9
CELL_SIZE = 60
BOARD_OFFSET_X = 50
BOARD_OFFSET_Y = 50
WINDOW_WIDTH = BOARD_OFFSET_X * 2 + BOARD_WIDTH * CELL_SIZE
WINDOW_HEIGHT = BOARD_OFFSET_Y * 2 + BOARD_HEIGHT * CELL_SIZE

# 색상
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (220, 20, 60)
GREEN = (50, 205, 50)
BLUE = (30, 144, 255)
LIGHT_BROWN = (240, 217, 181)
DARK_BROWN = (139, 69, 19)

# 플레이어
CHO = 0   # 초(紅, 아래쪽, 앞으로: y-1)
HAN = 1   # 한(藍, 위쪽, 앞으로: y+1)

# ------------------------------------------------------------
# 말 표시용 문자
# ------------------------------------------------------------
PIECE_CHAR = {
    CHO: {'K': '將', 'C': '車', 'H': '馬', 'E': '象', 'G': '士', 'A': '包', 'S': '卒'},
    HAN: {'K': '帥', 'C': '車', 'H': '馬', 'E': '象', 'G': '士', 'A': '包', 'S': '兵'}
}

# ------------------------------------------------------------
# 초기 배치 (board[y][x], 10행 x 9열)
#  위(한)                                                  아래(초)
# ------------------------------------------------------------
INITIAL_BOARD = [
    # y = 0 : 한 진영 뒷줄
    ['C', 'H', 'E', 'G', 'K', 'G', 'E', 'H', 'C'],
    # y = 1 : 포 라인
    ['.', 'A', '.', '.', '.', '.', '.', 'A', '.'],
    # y = 2 : 병 라인
    ['S', '.', 'S', '.', 'S', '.', 'S', '.', 'S'],
    # y = 3
    ['.', '.', '.', '.', '.', '.', '.', '.', '.'],
    # y = 4
    ['.', '.', '.', '.', '.', '.', '.', '.', '.'],
    # y = 5
    ['.', '.', '.', '.', '.', '.', '.', '.', '.'],
    # y = 6
    ['.', '.', '.', '.', '.', '.', '.', '.', '.'],
    # y = 7 : 초 졸 라인
    ['s', '.', 's', '.', 's', '.', 's', '.', 's'],
    # y = 8 : 초 포 라인
    ['.', 'a', '.', '.', '.', '.', '.', 'a', '.'],
    # y = 9 : 초 진영 뒷줄
    ['c', 'h', 'e', 'g', 'k', 'g', 'e', 'h', 'c'],
]

# ------------------------------------------------------------
# 보조 함수
# ------------------------------------------------------------
def in_bounds(x, y):
    return 0 <= x < BOARD_WIDTH and 0 <= y < BOARD_HEIGHT

def player_of(piece: str) -> int:
    if not piece or piece == '.':
        return -1
    return HAN if piece.isupper() else CHO

def piece_type(piece: str) -> str:
    return piece.upper()[0] if piece and piece != '.' else '.'

def in_palace(x: int, y: int) -> bool:
    """양쪽 궁(3x3) 내부 여부"""
    # 한의 궁: x 3~5, y 0~2
    # 초의 궁: x 3~5, y 7~9
    return (3 <= x <= 5 and 0 <= y <= 2) or (3 <= x <= 5 and 7 <= y <= 9)

def copy_board(board):
    return [row[:] for row in board]

def find_king(board, player):
    """해당 플레이어의 왕 위치 찾기"""
    for y in range(BOARD_HEIGHT):
        for x in range(BOARD_WIDTH):
            p = board[y][x]
            if p != '.' and piece_type(p) == 'K' and player_of(p) == player:
                return x, y
    return None

# ------------------------------------------------------------
# 말별 기초 이동 (체크 여부는 고려 X)
# ------------------------------------------------------------
def moves_chariot(board, x, y):
    """차(車) - 직선 무제한"""
    moves = []
    for dx, dy in [(1,0), (-1,0), (0,1), (0,-1)]:
        nx, ny = x + dx, y + dy
        while in_bounds(nx, ny):
            if board[ny][nx] == '.':
                moves.append((nx, ny))
            else:
                # 첫 장애물이 상대 말이면 거기까지만
                if player_of(board[ny][nx]) != player_of(board[y][x]):
                    moves.append((nx, ny))
                break
            nx += dx
            ny += dy
    return moves

def moves_cannon(board, x, y):
    """
    포(包)
    - 직선으로 이동
    - 반드시 '스크린(중간말)' 하나를 넘어서 상대 말만 잡기 가능
    - 포는 포를 넘을 수 없음, 포를 잡을 수도 없음
    - 빈칸으로 그냥 가는 이동은 허용하지 않는 버전
    """
    moves = []
    my_player = player_of(board[y][x])
    for dx, dy in [(1,0), (-1,0), (0,1), (0,-1)]:
        nx, ny = x + dx, y + dy
        screen_found = False
        while in_bounds(nx, ny):
            if board[ny][nx] != '.':
                # 스크린 찾는 단계
                if not screen_found:
                    # 스크린이 포이면 해당 방향 불가
                    if piece_type(board[ny][nx]) == 'A':
                        break
                    screen_found = True
                else:
                    # 스크린 이후 첫 말: 상대 말이고 포가 아니면 잡기 가능
                    if player_of(board[ny][nx]) != my_player and piece_type(board[ny][nx]) != 'A':
                        moves.append((nx, ny))
                    # 어쨌든 여기서 종료
                    break
            nx += dx
            ny += dy
    return moves

def moves_horse(board, x, y):
    """
    마(馬)
    - 1칸 직진 + 1칸 대각 (총 8방향)
    - 직진 방향의 '발'에 말이 있으면 해당 방향 불가
    """
    moves = []
    my_player = player_of(board[y][x])
    # (목적지, 발 위치) 세트
    patterns = [
        ((x+1, y+2), (x,   y+1)),
        ((x-1, y+2), (x,   y+1)),
        ((x+1, y-2), (x,   y-1)),
        ((x-1, y-2), (x,   y-1)),
        ((x+2, y+1), (x+1, y  )),
        ((x+2, y-1), (x+1, y  )),
        ((x-2, y+1), (x-1, y  )),
        ((x-2, y-1), (x-1, y  )),
    ]
    for (nx, ny), (bx, by) in patterns:
        if not in_bounds(nx, ny):
            continue
        if not in_bounds(bx, by):
            continue
        # 발이 막혀 있으면 불가
        if board[by][bx] != '.':
            continue
        # 도착지가 내 말이면 불가
        if board[ny][nx] != '.' and player_of(board[ny][nx]) == my_player:
            continue
        moves.append((nx, ny))
    return moves

def moves_elephant(board, x, y):
    """
    상(象) - 단순 버전: 대각 2칸
    (실제 장기 상의 세부적인 발 막힘 규칙은 더 복잡, 필요시 추가 구현 가능)
    """
    moves = []
    my_player = player_of(board[y][x])
    for dx, dy in [(2,2), (2,-2), (-2,2), (-2,-2)]:
        nx, ny = x + dx, y + dy
        if not in_bounds(nx, ny):
            continue
        # 중간 경로 한 칸(대충) 막힘 체크 (간단 버전)
        mx, my = x + dx//2, y + dy//2
        if not in_bounds(mx, my):
            continue
        # 중간에 말 있으면 막힘
        if board[my][mx] != '.':
            continue
        if board[ny][nx] != '.' and player_of(board[ny][nx]) == my_player:
            continue
        moves.append((nx, ny))
    return moves

def moves_king_or_guard(board, x, y):
    """
    장/수(將/帥, K) 와 사(士, G)
    - 궁 내부에서 상하좌우 + 대각 1칸
    """
    moves = []
    my_player = player_of(board[y][x])
    for dx, dy in [
        (1,0), (-1,0), (0,1), (0,-1),
        (1,1), (1,-1), (-1,1), (-1,-1)
    ]:
        nx, ny = x + dx, y + dy
        if not in_bounds(nx, ny):
            continue
        if not in_palace(nx, ny):
            continue
        if board[ny][nx] != '.' and player_of(board[ny][nx]) == my_player:
            continue
        moves.append((nx, ny))
    return moves

def moves_soldier(board, x, y):
    """
    졸/병(卒/兵)
    - 기본: 전진 1칸 + 좌/우 1칸
    - 강을 건넌 후(초: y <= 4, 한: y >= 5)에는 후진 1칸도 가능
    """
    moves = []
    p = board[y][x]
    my_player = player_of(p)
    dy_forward = -1 if my_player == CHO else 1

    # 전진
    fx, fy = x, y + dy_forward
    if in_bounds(fx, fy):
        if board[fy][fx] == '.' or player_of(board[fy][fx]) != my_player:
            moves.append((fx, fy))

    # 좌우 이동 (언제나 가능)
    for dx in (-1, 1):
        nx, ny = x + dx, y
        if in_bounds(nx, ny):
            if board[ny][nx] == '.' or player_of(board[ny][nx]) != my_player:
                moves.append((nx, ny))

    # 강을 건넌 뒤에는 후진 허용
    if (my_player == CHO and y <= 4) or (my_player == HAN and y >= 5):
        bx, by = x, y - dy_forward
        if in_bounds(bx, by):
            if board[by][bx] == '.' or player_of(board[by][bx]) != my_player:
                moves.append((bx, by))

    return moves

def get_raw_moves_for_piece(board, x, y):
    """체크/자기왕 보호는 고려하지 않은 '기초' 이동 목록"""
    p = board[y][x]
    if p == '.':
        return []
    t = piece_type(p)
    if t == 'C':   # 차
        return moves_chariot(board, x, y)
    elif t == 'A': # 포
        return moves_cannon(board, x, y)
    elif t == 'H': # 마
        return moves_horse(board, x, y)
    elif t == 'E': # 상
        return moves_elephant(board, x, y)
    elif t == 'K': # 장/수
        return moves_king_or_guard(board, x, y)
    elif t == 'G': # 사
        return moves_king_or_guard(board, x, y)
    elif t == 'S': # 졸/병
        return moves_soldier(board, x, y)
    return []

# ------------------------------------------------------------
# 체크 / 체크메이트 판정
# ------------------------------------------------------------
def kings_face_each_other(board):
    """
    장수 마주보기 룰:
    - 양쪽 왕이 같은 x(세로줄)에 있고
    - 그 사이에 말이 하나도 없으면 마주본 상태
    """
    pos_cho = find_king(board, CHO)
    pos_han = find_king(board, HAN)
    if not pos_cho or not pos_han:
        return False, None  # 게임 끝 등
    x1, y1 = pos_cho
    x2, y2 = pos_han
    if x1 != x2:
        return False, None
    # y 사이에 말이 있는지 확인
    sy, ey = sorted([y1, y2])
    for yy in range(sy+1, ey):
        if board[yy][x1] != '.':
            return False, None
    # 둘 다 같은 세로줄에서 마주봄
    return True, (x1, (y1, y2))

def is_in_check(board, player):
    """플레이어의 왕이 공격받고 있는지 여부"""
    king_pos = find_king(board, player)
    if not king_pos:
        return False
    kx, ky = king_pos
    opponent = 1 - player

    # 1) 상대 말들의 공격
    for y in range(BOARD_HEIGHT):
        for x in range(BOARD_WIDTH):
            p = board[y][x]
            if p == '.':
                continue
            if player_of(p) != opponent:
                continue
            for nx, ny in get_raw_moves_for_piece(board, x, y):
                if (nx, ny) == (kx, ky):
                    return True

    # 2) 장수 마주보기
    facing, _ = kings_face_each_other(board)
    if facing:
        # 마주보는 상황일 때, 양쪽 다 "체크"로 취급
        return True

    return False

def get_legal_moves_for_piece(board, x, y, player):
    """해당 말이 실제로 둘 수 있는 합법 수"""
    raw_moves = get_raw_moves_for_piece(board, x, y)
    legal_moves = []
    for nx, ny in raw_moves:
        # 같은 편 말이 있는 칸은 이미 필터링 되어 있지만, 안전하게 한 번 더 체크
        if board[ny][nx] != '.' and player_of(board[ny][nx]) == player:
            continue
        new_board = copy_board(board)
        new_board[ny][nx] = new_board[y][x]
        new_board[y][x] = '.'
        if not is_in_check(new_board, player):
            legal_moves.append((nx, ny))
    return legal_moves

def get_all_legal_moves(board, player):
    moves = []
    for y in range(BOARD_HEIGHT):
        for x in range(BOARD_WIDTH):
            p = board[y][x]
            if p == '.':
                continue
            if player_of(p) != player:
                continue
            for nx, ny in get_legal_moves_for_piece(board, x, y, player):
                moves.append(((x, y), (nx, ny)))
    return moves

def is_check(board, player):
    return is_in_check(board, player)

def is_checkmate(board, player):
    if not is_in_check(board, player):
        return False
    # 한 수도 둘 수 없으면 체크메이트
    return len(get_all_legal_moves(board, player)) == 0

# ------------------------------------------------------------
# 게임 클래스
# ------------------------------------------------------------
class JanggiGame:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        pygame.display.set_caption("한국 장기")
        self.clock = pygame.time.Clock()
        # 폰트: 맑은고딕 있으면 사용
        try:
            self.font = pygame.font.SysFont('malgungothic', 40, bold=True)
            self.small_font = pygame.font.SysFont('malgungothic', 28)
        except:
            self.font = pygame.font.Font(None, 40)
            self.small_font = pygame.font.Font(None, 28)

        self.board = copy_board(INITIAL_BOARD)
        self.current_player = CHO   # 초(紅) 선
        self.selected = None        # (x, y)
        self.valid_moves = []       # [(x, y), ...]
        self.game_over = False
        self.winner = None

    # 좌표 변환
    def pos_to_pixel(self, x, y):
        return BOARD_OFFSET_X + x * CELL_SIZE, BOARD_OFFSET_Y + y * CELL_SIZE

    def pixel_to_pos(self, px, py):
        x = (px - BOARD_OFFSET_X) // CELL_SIZE
        y = (py - BOARD_OFFSET_Y) // CELL_SIZE
        if in_bounds(x, y):
            return x, y
        return None

    # 그리기 관련
    def draw_board(self):
        self.screen.fill(LIGHT_BROWN)
        # 격자
        for x in range(BOARD_WIDTH + 1):
            pygame.draw.line(
                self.screen, DARK_BROWN,
                (BOARD_OFFSET_X + x * CELL_SIZE, BOARD_OFFSET_Y),
                (BOARD_OFFSET_X + x * CELL_SIZE, WINDOW_HEIGHT - BOARD_OFFSET_Y),
                2
            )
        for y in range(BOARD_HEIGHT + 1):
            pygame.draw.line(
                self.screen, DARK_BROWN,
                (BOARD_OFFSET_X, BOARD_OFFSET_Y + y * CELL_SIZE),
                (WINDOW_WIDTH - BOARD_OFFSET_X, BOARD_OFFSET_Y + y * CELL_SIZE),
                2
            )

        # 궁성 X자
        palace_lines = [
            ((3, 0), (5, 2)), ((3, 2), (5, 0)),
            ((3, 7), (5, 9)), ((3, 9), (5, 7))
        ]
        for (x1, y1), (x2, y2) in palace_lines:
            p1 = self.pos_to_pixel(x1, y1)
            p2 = self.pos_to_pixel(x2, y2)
            pygame.draw.line(self.screen, DARK_BROWN, p1, p2, 4)

    def draw_pieces(self):
        for y in range(BOARD_HEIGHT):
            for x in range(BOARD_WIDTH):
                p = self.board[y][x]
                if p == '.':
                    continue
                owner = player_of(p)
                color = RED if owner == CHO else BLUE
                char = PIECE_CHAR[owner][piece_type(p)]
                px, py = self.pos_to_pixel(x, y)
                text = self.font.render(char, True, color)
                tw, th = text.get_size()
                self.screen.blit(text, (px + (CELL_SIZE - tw)//2, py + (CELL_SIZE - th)//2))

    def draw_selection(self):
        if self.selected:
            sx, sy = self.selected
            rect = pygame.Rect(
                BOARD_OFFSET_X + sx*CELL_SIZE,
                BOARD_OFFSET_Y + sy*CELL_SIZE,
                CELL_SIZE, CELL_SIZE
            )
            pygame.draw.rect(self.screen, GREEN, rect, 4)
            for tx, ty in self.valid_moves:
                rx = BOARD_OFFSET_X + tx*CELL_SIZE + CELL_SIZE//4
                ry = BOARD_OFFSET_Y + ty*CELL_SIZE + CELL_SIZE//4
                pygame.draw.ellipse(
                    self.screen, GREEN,
                    (rx, ry, CELL_SIZE//2, CELL_SIZE//2)
                )

    def draw_status(self):
        status = f"현재 차례: {'초(紅)' if self.current_player == CHO else '한(藍)'}"
        if self.game_over:
            status = f"게임 종료: {'초(紅)' if self.winner == CHO else '한(藍)'} 승리!"
        else:
            # 체크 여부 표시
            if is_check(self.board, self.current_player):
                status += "  (장군!)"
        text = self.small_font.render(status, True, BLACK)
        self.screen.blit(text, (20, 10))

    # 입력 처리
    def handle_click(self, pos):
        if self.game_over:
            return
        grid_pos = self.pixel_to_pos(*pos)
        if not grid_pos:
            return
        x, y = grid_pos
        p = self.board[y][x]

        # 이미 선택된 말이 있을 때
        if self.selected:
            if (x, y) in self.valid_moves:
                sx, sy = self.selected
                # 이동 수행
                self.board[y][x] = self.board[sy][sx]
                self.board[sy][sx] = '.'
                self.selected = None
                self.valid_moves = []

                # 차례 변경
                self.current_player = 1 - self.current_player

                # 체크메이트 판정
                if is_checkmate(self.board, self.current_player):
                    self.game_over = True
                    self.winner = 1 - self.current_player
                return
            else:
                # 선택 취소 후, 다시 시도(해당 칸에 내 말이 있으면 재선택)
                self.selected = None
                self.valid_moves = []
                # 아래에서 새 선택 로직 진행

        # 새로 말 선택
        if p != '.' and player_of(p) == self.current_player:
            self.selected = (x, y)
            self.valid_moves = get_legal_moves_for_piece(self.board, x, y, self.current_player)
        else:
            self.selected = None
            self.valid_moves = []

    def run(self):
        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    self.handle_click(event.pos)

            self.draw_board()
            self.draw_pieces()
            self.draw_selection()
            self.draw_status()
            pygame.display.flip()
            self.clock.tick(60)

if __name__ == "__main__":
    game = JanggiGame()
    game.run()

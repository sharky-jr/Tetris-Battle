import random
from shape_formats import shape_colors, shapes
import csv
import contextlib
import os
with contextlib.redirect_stdout(None):
    import pygame


class Hold:
    global win

    def __init__(self, ):
        self.show = False
        self.available = True
        self.held_piece = None

    def draw(self, g):
        sx = g.sx - g.play_w - block_size * 8
        sy = g.sy + block_size * 10
        if self.show:
            for i, line in enumerate(self.held_piece.shape[0]):
                row = list(line)
                for j, column in enumerate(row):
                    if column == "0":
                        pygame.draw.rect(win, self.held_piece.color,
                                         (sx + j * block_size, sy + i * block_size, block_size, block_size), 0)
        fonts = pygame.font.SysFont('ComicSans', 30)
        win.blit(fonts.render("Hold", 1, white), (sx + 40, sy - 30))

    def action(self, current_piece, next_piece, s1):
        i = -1
        if self.available:
            if self.show:
                temp = current_piece
                current_piece = self.held_piece
                self.held_piece = temp
                i = -1
            else:
                self.held_piece = current_piece
                current_piece = next_piece
                next_piece, i = get_shape(s1)
            current_piece.x = 5
            current_piece.y = 0
            self.show = True
            self.available = False
        return current_piece, next_piece, i


class Piece(object):
    def __init__(self, x, y, shape):
        self.x = x
        self.y = y
        self.shape = shape
        self.color = shape_colors[shapes.index(shape)]
        self.rotation = 0


class GameThread(object):
    def __init__(self, player, x, y, seed, seed2):
        self.player = player
        self.x = x
        self.y = y
        self.play_w = block_size*10
        self.play_h = block_size*20
        self.grid = []
        self.sx = self.x + 7 * self.play_w / 6
        self.sy = self.y + self.play_h / 2 - self.play_h / 3
        self.score = 0
        self.cleared_lines = 0
        self.level = 1
        self.tetris_rate = 0
        self.drought = 0
        self.tetris_score = 0
        self.fall_speed = 0.5
        self.seed = seed
        self.seed2 = seed2
        self.current_piece, _ = get_shape(self.seed2)
        self.change_piece = False
        self.locked_positions = {}
        self.next_piece, self.index = get_shape(self.seed)
        self.seed, self.seed2 = shuffle(self.seed, self.seed2, self.index)
        self.fall_time = 0
        self.next_level = 10
        self.play = True
        self.hold_instance = Hold()

    def run(self):
        global clock, scores
        game1 = True
        self.grid = create_grid(self.locked_positions)
        self.reset()

        while game1:
            self.fall_time += clock.get_rawtime()
            clock.tick(60)
            self.grid = create_grid(self.locked_positions)
            if self.cleared_lines >= self.next_level:
                self.fall_speed -= 0.01
                self.next_level += 10

            if self.fall_time / 1000 >= self.fall_speed and self.play:
                self.fall_time = 0
                self.current_piece.y += 1
                if not (valid_space(self.current_piece, self.grid)) and self.current_piece.y > 0:
                    change_sound.play()
                    self.current_piece.y -= 1
                    self.change_piece = True

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    game1 = False

                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_LEFT:
                        self.current_piece.x -= 1
                        if not (valid_space(self.current_piece, self.grid)):
                            self.current_piece.x += 1
                    elif event.key == pygame.K_RIGHT:
                        self.current_piece.x += 1
                        if not (valid_space(self.current_piece, self.grid)):
                            self.current_piece.x -= 1
                    elif event.key == pygame.K_DOWN:
                        self.current_piece.y += 1
                        self.score += 1
                        if not (valid_space(self.current_piece, self.grid)):
                            self.current_piece.y -= 1
                            self.score -= 1
                    elif event.key == pygame.K_UP:
                        self.current_piece.rotation += 1
                        if not (valid_space(self.current_piece, self.grid)):
                            self.current_piece.rotation -= 1
                    elif event.key == pygame.K_ESCAPE:
                        return False
                    elif event.key == pygame.K_BACKSPACE:
                        return True
                    elif event.key == pygame.K_SPACE:
                        if self.hold_instance.available and hold:
                            self.current_piece, self.next_piece, index = self.hold_instance.action(self.current_piece,
                                                                                                   self.next_piece,
                                                                                                   self.seed)
                            self.seed, self.seed2 = shuffle(self.seed, self.seed2, index)
                    elif event.key == pygame.K_RCTRL:
                        self.drop()
            shape_pos = convert_shape_format(self.current_piece)
            for i in range(len(shape_pos)):
                x, y = shape_pos[i]
                if y > -1:
                    self.grid[y][x] = self.current_piece.color

            if self.change_piece:
                self.hold_instance.available = True
                for pos in shape_pos:
                    p = (pos[0], pos[1])
                    self.locked_positions[p] = self.current_piece.color
                self.current_piece = self.next_piece
                if self.current_piece.shape == shapes[2]:
                    self.drought = 0
                else:
                    self.drought += 1
                self.next_piece, index = get_shape(self.seed)
                self.seed, self.seed2 = shuffle(self.seed, self.seed2, index)
                self.change_piece = False
                increment = clear_rows(self.grid, self.locked_positions)
                if increment == 4:
                    tetris_sound.play()
                    win.fill((128, 128, 128))
                    self.draw_text_middle('TETRIS!', 70, (255, 0, 0), win)
                    pygame.display.update()
                    pygame.time.delay(100)
                self.update_score(increment)
            win.fill((0, 0, 0))
            self.draw_window(win)
            self.draw_next_shape(self.next_piece, win)
            self.score_gap(int(top_score))
            # self.draw_shadow()
            if hold:
                self.hold_instance.draw(self)
            pygame.display.update()
            if check_lost(self.locked_positions):
                self.draw_text_middle("You Lost!", 80, white, win)
                pygame.display.update()
                pygame.time.delay(1500)
                player_name, updated = ask_name(self.player, self.score, battle_mode=False)
                if updated:
                    scores = self.save_score(player_name)
                self.reset()
                return True

    def draw_shadow(self):
        # y = self.y_project()
        for i, line in enumerate(self.current_piece.shape[self.current_piece.rotation % len(self.current_piece.shape)]):
            row = list(line)
            for j, column in enumerate(row):
                if column == "0":
                    pygame.draw.rect(win, white,
                                     (self.current_piece.x + j * block_size, self.current_piece.y + i * block_size, block_size, block_size), 0)

    def y_project(self):
        drop = True
        while drop:
            temp = self.current_piece.y
            self.current_piece.y += 1
            if not (valid_space(self.current_piece, self.grid)):
                self.current_piece.y -= 1
                result = self.current_piece.y
                self.current_piece.y = temp
                return result

    def drop(self):
        drop = True
        while drop:
            self.current_piece.y += 1
            self.score += 1
            if not(valid_space(self.current_piece, self.grid)):
                self.current_piece.y -= 1
                self.score -= 1
                drop = False

    def save_score(self, name):
        new_scores = []
        updated = False
        for each in scores:
            if self.score >= each[1] and not updated:
                new_scores.append([name, self.score, self.level])
                updated = True
            new_scores.append(each)
        if updated:
            new_scores.pop(len(new_scores)-1)
            with open('Highscores.csv', 'w', newline='') as f:
                file = csv.writer(f)
                for score in new_scores:
                    file.writerow(score)
        return new_scores

    def draw_text_middle(self, text, size, color, surface):
        font1 = pygame.font.SysFont("comicsans", size, bold=True)
        render = font1.render(text, 1, color)
        surface.blit(render, (self.x + self.play_w / 2 - render.get_width() / 2, height / 2 - render.get_height() / 2))

    def draw_grid(self, surface, g):
        sx = self.x
        sy = self.y

        for i in range(len(g)):
            pygame.draw.line(surface, (128, 128, 128), (sx, sy + i * block_size),
                             (sx + self.play_w, sy + i * block_size))
            for j in range(len(g[i])):
                pygame.draw.line(surface, (128, 128, 128), (sx + j * block_size, sy + i * block_size),
                                 (sx + j * block_size, sy + self.play_h))

    def draw_next_shape(self, shape, surface):

        render = font2.render('Next Shape: ', 1, white)
        form = shape.shape[shape.rotation % len(shape.shape)]

        for i, line in enumerate(form):
            row = list(line)
            for j, column in enumerate(row):
                if column == "0":
                    pygame.draw.rect(surface, shape.color,
                                     (self.sx + j * block_size, self.sy + (i+1) * block_size, block_size, block_size),
                                     0)
        surface.blit(render, (self.sx + block_size/3, self.sy - block_size*2))

    def draw_window(self, surface):
        # surface.fill((0, 0, 0))
        global font
        render = font.render('Tetris', 1, white)
        surface.blit(render, (self.x + self.play_w / 2 - (render.get_width() / 2), y_title))
        score_label = font2.render('Score: ' + str(self.score), 1, white)
        lines_label = font2.render('Lines: ' + str(self.cleared_lines), 1, white)
        surface.blit(score_label, (self.sx + block_size, self.sy + block_size*8))
        surface.blit(lines_label, (self.sx + block_size, self.sy + block_size*9))
        surface.blit(font2.render('Level: ' + str(self.level), 1, white), (self.sx + block_size, self.sy))
        surface.blit(font2.render('High Score: ' + str(top_score), 1, white), (self.x-block_size*6-10,
                                                                                         self.sy))
        surface.blit(font2.render('Tetris rate: ' + str(self.tetris_rate) + '%', 1, white),
                     (self.x-block_size*6, self.y + 200))
        surface.blit(font2.render('Drought: ' + str(self.drought), 1, white), (self.x-block_size*6,
                                                                                         self.y + 230))
        for i in range(len(self.grid)):
            for j in range(len(self.grid[i])):
                pygame.draw.rect(surface, self.grid[i][j],
                                 (self.x + j * block_size, self.y + i * block_size, block_size,
                                  block_size), 0)
        pygame.draw.rect(surface, (255, 0, 0), (self.x, self.y, self.play_w, self.play_h), 4)
        self.draw_grid(surface, self.grid)

    def score_gap(self, score):
        gap = self.score - score
        if gap == 0:
            color = white
            strings = ''
        elif gap < 0:
            color = red
            strings = '-'
        else:
            color = green
            strings = '+'
        strings += str(abs(gap))
        r = font2.render(strings, 1, color)
        win.blit(r, (self.sx + block_size + block_size, self.sy + block_size*7))

    def update_score(self, inc):
        self.cleared_lines += inc
        self.level = int(self.cleared_lines / 10) + 1
        if inc == 1:
            self.score += 100 * self.level
        elif inc == 2:
            self.score += 300 * self.level
        elif inc == 3:
            self.score += 500 * self.level
        elif inc == 4:
            self.score += 800 * self.level
            self.tetris_score += 4
        if self.cleared_lines != 0:
            self.tetris_rate = self.tetris_score / self.cleared_lines * 100
            self.tetris_rate = int(self.tetris_rate)

    def reset(self):
        self.fall_speed = 0.5
        self.score = 0
        self.cleared_lines = 0
        self.tetris_score = 0
        self.tetris_rate = 0
        self.drought = 0
        self.seed, self.seed2 = shuffle(self.seed, self.seed2, 6)


class Button:
    def __init__(self):
        self.active = False
        self.color = [grey, blue]

    def draw(self, x, y, w, h, text):
        pygame.draw.rect(win, self.color[int(self.active)], (int(x - (w * 0.25)), int(y - h * 0.05), int(w * 1.5),
                                                             int(h * 1.1)))
        win.blit(text, (x, y))


def load_scores():
    with open('Highscores.csv', 'r', newline='') as f:
        file = csv.reader(f)
        score = []
        max_score = 0
        for index, row in enumerate(file):
            score.append([row[0], int(row[1]), int(row[2])])
            if index == 0:
                max_score = row[1]
    return score, max_score


def render_scores():
    score = []
    for index, row in enumerate(scores):
        score.append(menu_font.render(str(index+1)+'-   '+str(row[0])+': '+str(row[1]) + ' l.' + str(row[2]), 1, black))
    return score


def shuffle(a, b, i):
    random.seed(b)
    rand = random.randrange(0, 1000)
    b = a
    a = i * 3 + rand
    return a, b


def play_song():
    pygame.mixer.music.load(os.path.join('Sounds', 'Tetris.mp3'))
    pygame.mixer.music.play(loops=-1)


black = (0, 0, 0)
blue = (90, 90, 200)
white = (250, 250, 250)
grey = (128, 128, 128)
red = (200, 0, 0)
green = (0, 200, 0)

game = None
pygame.mixer.pre_init(44100, -16, 2, 2048)
pygame.mixer.init()
pygame.init()
# https://stackoverflow.com/questions/42598830/wrong-fullscreen-resolution-with-pygame-on-osx
infos = pygame.display.Info()
screen_size = (infos.current_w, infos.current_h)
win = pygame.display.set_mode(screen_size, pygame.FULLSCREEN | pygame.HWSURFACE)
width = pygame.display.get_surface().get_width()
height = pygame.display.get_surface().get_height()
clock = pygame.time.Clock()
block_size = int(height/36)
title_font = pygame.font.SysFont('cambria', int(height/12))
menu_font = pygame.font.SysFont('candara', int(height/16))
font = pygame.font.SysFont('comicsansms', block_size+10)
font2 = pygame.font.SysFont('comicsans', block_size)
label = 'Tetris Battle'
menu = ['Single Player', '2 Players', 'HighScores', 'Options', 'Quit']
options_list = ['Hold: ', 'Music: ', 'Back']
menu_render = []
buttons = []
scores, top_score = load_scores()
pygame.display.set_caption(label)
label_render = title_font.render(label, 1, blue)
x_title = int(width/2-label_render.get_width()/2)
y_title = int(label_render.get_height()*1.4)
tetris_sound = pygame.mixer.Sound(os.path.join('Sounds', 'Tetris.wav'))
change_sound = pygame.mixer.Sound(os.path.join('Sounds', 'change_piece.wav'))
for obj in menu:
    menu_render.append(menu_font.render(obj, 1, white))
    buttons.append(Button())
run = True
music = True
hold = True
play_song()


def players_controls(event):
    global game
    # Player 2 controls
    if event.key == pygame.K_UP:
        game[1].current_piece.rotation += 1
        if not (valid_space(game[1].current_piece, game[1].grid)):
            game[1].current_piece.rotation -= 1
    if event.key == pygame.K_DOWN:
        game[1].current_piece.y += 1
        game[1].score += 1
        if not (valid_space(game[1].current_piece, game[1].grid)):
            game[1].current_piece.y -= 1
            game[1].score -= 1
    if event.key == pygame.K_LEFT:
        game[1].current_piece.x -= 1
        if not (valid_space(game[1].current_piece, game[1].grid)):
            game[1].current_piece.x += 1
    if event.key == pygame.K_RIGHT:
        game[1].current_piece.x += 1
        if not (valid_space(game[1].current_piece, game[1].grid)):
            game[1].current_piece.x -= 1
    if event.key == pygame.K_RCTRL:
        game[1].drop()
    if event.key == pygame.K_RSHIFT:
        if game[1].hold_instance.available and hold:
            game[1].current_piece, game[1].next_piece, index = game[1].hold_instance.action(game[1].current_piece,
                                                                                            game[1].next_piece,
                                                                                            game[1].seed)
            game[1].seed, game[1].seed2 = shuffle(game[1].seed, game[1].seed2, index)

    # Player 1 controls
    if event.key == pygame.K_w:
        game[0].current_piece.rotation += 1
        if not (valid_space(game[0].current_piece, game[0].grid)):
            game[0].current_piece.rotation -= 1
    if event.key == pygame.K_s:
        game[0].current_piece.y += 1
        game[0].score += 1
        if not (valid_space(game[0].current_piece, game[0].grid)):
            game[0].current_piece.y -= 1
            game[0].score -= 1
    if event.key == pygame.K_a:
        game[0].current_piece.x -= 1
        if not (valid_space(game[0].current_piece, game[0].grid)):
            game[0].current_piece.x += 1
    if event.key == pygame.K_d:
        game[0].current_piece.x += 1
        if not (valid_space(game[0].current_piece, game[0].grid)):
            game[0].current_piece.x -= 1
    if event.key == pygame.K_SPACE:
        if game[0].hold_instance.available and hold:
            game[0].current_piece, game[0].next_piece, index = game[0].hold_instance.action(game[0].current_piece,
                                                                                            game[0].next_piece,
                                                                                            game[0].seed)
            game[0].seed, game[0].seed2 = shuffle(game[0].seed, game[0].seed2, index)
    if event.key == pygame.K_c:
        game[0].drop()


def create_grid(locked_positions):
    grid = [[(0, 0, 0) for _ in range(10)] for _ in range(20)]
    for i in range(len(grid)):
        for j in range(len(grid[i])):
            if (j, i) in locked_positions:
                c = locked_positions[(j, i)]
                grid[i][j] = c
    return grid


def convert_shape_format(shape):
    positions = []
    formatting = shape.shape[shape.rotation % len(shape.shape)]
    for i, line in enumerate(formatting):
        row = list(line)
        for j, column in enumerate(row):
            if column == '0':
                positions.append((shape.x + j, shape.y + i))

    for i, pos in enumerate(positions):
        positions[i] = (pos[0] - 2, pos[1] - 4)
    return positions


def valid_space(shape, gri):
    accepted_pos = [[(j, i) for j in range(10) if gri[i][j] == (0, 0, 0)]for i in range(20)]
    accepted_pos = [j for sub in accepted_pos for j in sub]
    formatted = convert_shape_format(shape)

    for pos in formatted:
        if pos[0] < 0 or pos[0] > 9:
            return False
        if pos not in accepted_pos:
            if pos[1] > -1:
                return False
    return True


def check_lost(positions):
    for pos in positions:
        x, y = pos
        if y < 1:
            return True
    return False


def get_shape(seed):
    random.seed(seed)
    index = random.randrange(0, len(shapes))
    return Piece(5, 1, shapes[int(random.uniform(0, 6))]), index


def clear_rows(grid, locked):

    inc = 0
    indices = []
    for i in range(len(grid)-1, -1, -1):
        row = grid[i]
        if (0, 0, 0) not in row:
            inc += 1
            indices.append(i)
            for j in range(len(row)):
                del locked[(j, i)]

    if inc > 0:
        for ind in reversed(indices):
            for key in sorted(list(locked), key=lambda xx: xx[1])[::-1]:
                x, y = key
                if y < ind:

                    new_key = (x, y + 1)
                    locked[new_key] = locked.pop(key)
    return inc


def draw_menu(menu_input, button_input, shape_stream, offset):
    win.fill(black)
    for i, stream in enumerate(shape_stream):
        draw_stream(stream, (i-1)*5*block_size, offset[i], int(offset[i]/block_size))
    win.blit(label_render, (x_title, y_title))
    i = 0
    for item, button in zip(menu_input, button_input):
        h = item.get_height()
        w = item.get_width()
        x = width/2 - w/2
        y = height/2 - h + i - 50
        i += int(h*1.5)
        button.draw(x, y, w, h, item)
    pygame.display.update()


def check_active():
    active = False
    i = 0
    for index, each in enumerate(buttons):
        if each.active:
            active = True
            i = index
    return active, i


def create_stream():
    stream = []
    for _ in range(4):
        temp, _ = get_shape(random.randrange(0, 100))
        stream.append(temp)
    return stream


def main_menu():
    global run
    rain = [create_stream() for _ in range(15)]
    offset = [block_size * random.randrange(3, 10) for _ in range(len(rain))]
    while run:
        clock.tick(30)
        active, i = check_active()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False, -1
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return False, -1
                elif event.key == pygame.K_DOWN:
                    if active:
                        buttons[i].active = False
                        buttons[(i + 1) % (len(buttons))].active = True
                    else:
                        buttons[0].active = True
                elif event.key == pygame.K_UP:
                    if active:
                        buttons[i].active = False
                        buttons[(i - 1) % (len(buttons))].active = True
                    else:
                        buttons[-1].active = True
                elif event.key == pygame.K_SPACE or event.key == pygame.K_RETURN:
                    if buttons[i].active:
                        return True, i
        draw_menu(menu_render, buttons, rain, offset)


def draw_scores(score, title):
    win.fill(blue)
    win.blit(title, (x_title+25, y_title-25))
    for i, each in enumerate(score):
        win.blit(each, (width/2 - each.get_width()/2, y_title + title.get_height() + i*each.get_height()))
    pygame.display.update()


def high_scores():
    render = title_font.render(menu[2], 1, black)
    while True:
        clock.tick(30)
        for event in pygame.event.get():
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return False
                elif event.key == pygame.K_BACKSPACE:
                    return True
        scores_render = render_scores()
        draw_scores(scores_render, render)


def single_player():
    global game
    r1 = random.randrange(0, 50)
    r2 = random.randrange(0, 48)
    game = GameThread(1, width/2 - block_size*5, int(height/2 - block_size*10), r1, r2)
    c = game.run()
    return c


def battle():
    global game, scores
    r1 = random.randrange(0, 50)
    r2 = random.randrange(0, 48)
    game = [GameThread(1, block_size*10, int(height/2 - block_size*10), r1, r2),
            GameThread(2, width-block_size*20, int(height/2 - block_size*10), r1, r2)]
    run_game = True
    end = True
    while run_game:
        clock.tick(60)
        win.fill((0, 0, 0))
        for each in game:
            each.fall_time += clock.get_rawtime()
            each.grid = create_grid(each.locked_positions)
            if each.cleared_lines >= each.next_level:
                each.fall_speed -= 0.01
                each.next_level += 10

            if each.fall_time / 1000 >= each.fall_speed and each.play:
                each.fall_time = 0
                each.current_piece.y += 1
                if not (valid_space(each.current_piece, each.grid)) and each.current_piece.y > 0:
                    change_sound.play()
                    each.current_piece.y -= 1
                    each.change_piece = True
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run_game = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_BACKSPACE:
                    end = False
                    run_game = False
                if event.key == pygame.K_ESCAPE:
                    run_game = False
                players_controls(event)
        for each in game:
            shape_pos = convert_shape_format(each.current_piece)
            for i in range(len(shape_pos)):
                x, y = shape_pos[i]
                if y > -1:
                    each.grid[y][x] = each.current_piece.color

            if each.change_piece and each.play:
                each.hold_instance.available = True
                for pos in shape_pos:
                    p = (pos[0], pos[1])
                    each.locked_positions[p] = each.current_piece.color
                each.current_piece = each.next_piece
                if each.current_piece.shape == shapes[2]:
                    each.drought = 0
                else:
                    each.drought += 1
                each.next_piece, index = get_shape(each.seed)
                each.seed, each.seed2 = shuffle(each.seed, each.seed2, index)
                each.change_piece = False
                increment = clear_rows(each.grid, each.locked_positions)
                if increment == 4:
                    tetris_sound.play()
                    win.fill((128, 128, 128))
                    each.draw_text_middle('TETRIS!', 70, (255, 0, 0), win)
                    pygame.display.update()
                    pygame.time.delay(100)
                each.update_score(increment)
            each.draw_window(win)
            each.draw_next_shape(each.next_piece, win)
            y = (-1 * each.player) + 2
            each.score_gap(game[y].score)
            if hold:
                each.hold_instance.draw(each)
            if check_lost(each.locked_positions):
                each.play = False
                each.draw_text_middle("You Lost!", 80, white, win)
        if not game[0].play and not game[1].play:
            for each in game:
                player_name, updated = ask_name(each.player, each.score, battle_mode=True)
                if updated:
                    scores = each.save_score(player_name)
                each.reset()
                end = False
                run_game = False
        pygame.display.update()
    return end


def ask_name(n, score, battle_mode):
    if battle_mode:
        render = menu_font.render('Player '+str(n)+', please enter your name:', 1, white)
    else:
        render = menu_font.render('Please enter your name:', 1, white)
    r = True
    c = False
    player_name = 'Player ' + str(n)
    for each in scores:
        if score >= each[1]:
            c = True
    input_string = ''
    while r and c:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                r = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    r = False
                if event.key == pygame.K_RETURN:
                    player_name = input_string
                    r = False
                elif event.key == pygame.K_BACKSPACE:
                    input_string = input_string[:-1]
                else:
                    input_string += event.unicode
        win.fill((0, 0, 0))
        sx = render.get_width()/2+40
        sy = height/3
        win.blit(render, (sx, sy))
        win.blit(menu_font.render(input_string, 1, white), (sx, sy + render.get_height()))
        pygame.display.update()

    return player_name, c


def options():
    selection = 0
    rain = [create_stream() for _ in range(15)]
    offset = [block_size * random.randrange(3, 10) for _ in range(len(rain))]
    global music, hold
    while True:
        settings_string = generate_string()
        settings_string.append('')
        options_render = []
        options_buttons = []
        for item, state in zip(options_list, settings_string):
            options_render.append(menu_font.render(item + state, 1, white))
            options_buttons.append(Button())
        clock.tick(30)
        for event in pygame.event.get():
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return False
                elif event.key == pygame.K_BACKSPACE:
                    return True
                elif event.key == pygame.K_DOWN:
                    options_buttons[selection % len(options_render)].active = False
                    selection += 1
                elif event.key == pygame.K_UP:
                    options_buttons[selection % len(options_render)].active = False
                    selection -= 1
                elif event.key == pygame.K_SPACE or event.key == pygame.K_RETURN:
                    if selection % len(options_render) == 0:
                        hold = not hold
                    elif selection % len(options_render) == 1:
                        music = not music
                        if music:
                            play_song()
                        else:
                            pygame.mixer_music.stop()
                    else:
                        return True

        options_buttons[selection % 3].active = True
        draw_menu(options_render, options_buttons, rain, offset)


def generate_string():
    settings = []
    if hold:
        settings.append('On')
    else:
        settings.append('Off')
    if music:
        settings.append('On')
    else:
        settings.append('Off')
    return settings


def draw_shape(shape, surface, sx, sy):

    form = shape.shape[shape.rotation % len(shape.shape)]

    for i, line in enumerate(form):
        row = list(line)
        for j, column in enumerate(row):
            if column == "0":
                pygame.draw.rect(surface, shape.color,
                                 (sx + j * block_size, (sy % height) + (i+1) * block_size, block_size, block_size), 0)


def draw_stream(shape_stream, x, offset, speed):
    for j, shape in enumerate(shape_stream):
        draw_shape(shape, win, x, offset + shape.y + j * block_size * 9)
        shape.y += speed

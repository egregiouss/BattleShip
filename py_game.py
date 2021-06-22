import pygame
import random
import ui
from ui import UIManager, DrawManager

GAME_WITH_BOT = False


class Field:
    def __init__(self, field_params):
        self.taken = []
        self.available = []
        self.field_size = field_params.field_size
        self.nums_of_ships = field_params.nums_of_ships
        # индекс + 1 - длина корабля, значение - количество таких кораблей
        self.cells_state = dict()
        self.set_cells_state()
        self.ships_to_draw = []
        self.ships = dict()

    # делает все клетки поля пустыми, доступными
    def set_cells_state(self):
        self.cells_state = dict()
        for x in range(1, self.field_size + 1):
            for y in range(1, self.field_size + 1):
                self.cells_state[(x, y)] = True

    # метод генерации кораблей.
    def generate_ships(self, ui_manager):
        self.uiManager = ui_manager
        self.field_size = ui_manager.field_params.field_size
        self.nums_of_ships = ui_manager.field_params.nums_of_ships

        self.ships = {}
        self.set_cells_state()
        self.ships_to_draw = []
        self.update_available()

        self.uiManager.next_window(0)

        self.generation()

        for ship in self.ships_to_draw:
            self.uiManager.drawer.draw_ship(ship[0], ship[1])

    def generation(self):
        start_again = False
        while len(self.ships_to_draw) < \
                self.uiManager.field_params.total_amount_of_ships:
            for i in range(len(self.nums_of_ships) - 1, -1, -1):
                s = 0
                while s < self.nums_of_ships[i]:
                    if len(self.available) == 0 or \
                            len(self.taken) == len(self.available):
                        start_again = True
                        break
                    (x, y) = random.choice(self.available)
                    if (x, y) not in self.taken:
                        self.taken.append((x, y))
                        horizontal = bool(random.randint(0, 1))
                        if horizontal:
                            possible_ships = [[(x + z, y) for z in
                                               range(j, i + 1 + j)] for j in
                                              range(0, -(i + 1), -1)]
                        else:
                            possible_ships = [[(x, y + z) for z in
                                               range(j, i + 1 + j)] for j in
                                              range(0, -(i + 1), -1)]
                        for ship in possible_ships:
                            if self.is_ship_can_be_put(ship):
                                self.add_ship(ship, int(horizontal))
                                s += 1
                                break
                if start_again:
                    start_again = False
                    self.ships = {}
                    self.set_cells_state()
                    self.ships_to_draw = []
                    self.update_available()
                    self.uiManager.next_window(0)
                    break

    def update_available(self):
        self.available = []
        for key in self.cells_state.keys():
            if self.cells_state[key]:
                self.available.append(key)

    def is_ship_can_be_put(self, ship):
        for cell in ship:
            if cell not in self.cells_state.keys() or \
                    not self.cells_state[cell]:
                return False
        return True

    # добавляет корабль в словарь кораблей
    def add_ship(self, ship, turn):
        for cell in ship:
            x = cell[0]
            y = cell[1]
            neighbours = []
            for n in ship:
                if n == cell:
                    continue
                neighbours.append(n)
            self.disable_cells(x, y)
            self.ships[(x, y)] = (False, neighbours)
        self.ships_to_draw.append((ship, turn))
        self.taken = []

    def remove_ship(self, last_ship):
        ship = last_ship[0]
        for cell in ship:
            x = cell[0]
            y = cell[1]
            del self.ships[(x, y)]
            cells_around = [(x + i, y + j) for i in range(-1, 2) for j in
                            range(-1, 2)]
            for c in cells_around:
                if c[0] < 1 or c[0] > self.field_size or c[1] < 1 or \
                        c[1] > self.field_size:
                    continue
                self.cells_state[c] = True

    def disable_cells(self, x, y):
        cells_around = [(x + i, y + j) for i in range(-1, 2) for j in
                        range(-1, 2)]
        for cell in cells_around:
            if cell[0] < 1 or cell[0] > self.field_size or cell[1] < 1 or \
                    cell[1] > self.field_size:
                continue
            self.cells_state[cell] = False
            if cell in self.available:
                self.available.remove(cell)


class Player:
    def __init__(self, ui_manager):
        self.uiManager = ui_manager
        self.field = Field(self.uiManager.field_params)
        self.score = 0

    def do_shot(self, event, offset):
        offset_for_field = self.uiManager.field_params.offset
        x, y = event.pos
        if (offset + offset_for_field) * \
                ui.cell_size <= x <= \
                (self.uiManager.field_params.field_size + offset +
                 offset_for_field) * \
                ui.cell_size and ui.top_margin + \
                offset_for_field * \
                ui.cell_size <= y <= \
                ui.top_margin + (self.uiManager.field_params.field_size +
                                 offset_for_field) * \
                ui.cell_size:
            fired_cell = (
                int(x / ui.cell_size
                    + 1 - offset - offset_for_field),
                int((y - ui.top_margin) / ui.cell_size
                    + 1 - offset_for_field))
            return fired_cell
        else:
            return 0, 0


class Bot:
    def __init__(self, difficulty, field_params):
        self.level = difficulty
        self.last_shot_good = False
        self.last_shot = (0, 0)
        self.last_good_shot = (0, 0)
        self.recommendation = []
        self.killed = False
        self.field = Field(field_params)
        self.score = 0

    def do_shot(self, enemy, level):
        if level == 2:
            target = self.do_shot_level_2(enemy)
        elif level == 1:
            target = self.do_shot_level_1(enemy)
        else:
            target = self.do_shot_level_3(enemy)
        return target[0], target[1]

    def do_shot_level_2(self, enemy):
        available = []
        for key in enemy.field.cells_state.keys():
            if enemy.field.cells_state[key]:
                available.append(key)
        self.last_shot_good = self.last_shot in enemy.field.ships
        if self.last_good_shot != (0, 0) and not self.killed:
            crd = self.last_good_shot
            crd_rec = [[crd[0] - 1, crd[1]], [crd[0] + 1, crd[1]],
                       [crd[0], crd[1] - 1], [crd[0], crd[1] + 1]]
            crd_rec = filter(lambda x: 1 <= x[0] <= enemy.field.field_size and
                             1 <= x[1] <= enemy.field.field_size, crd_rec)
            crd_rec = filter(lambda x: (x[0], x[1]) in available, crd_rec)
            self.recommendation.extend(crd_rec)
            if len(self.recommendation) == 0:
                target = random.choice(available)
            else:
                target = self.recommendation.pop()
        else:
            target = random.choice(available)
        if self.killed:
            self.recommendation = []
            self.last_good_shot = (0, 0)

        return target

    @staticmethod
    def do_shot_level_1(enemy):
        available = []
        for key in enemy.field.cells_state.keys():
            if enemy.field.cells_state[key]:
                available.append(key)
        return random.choice(available)

    @staticmethod
    def do_shot_level_3(enemy):
        available = []
        if len(available) == 0:
            for key in enemy.field.ships.keys():
                if enemy.field.cells_state[key]:
                    available.append(key)
        return random.choice(available) if random.randint(0, 1) == 0 else \
            random.choice(list(enemy.field.cells_state.keys()))


class ShootingManager:
    def __init__(self, player_num, player, ui_manager):
        self.player = player
        self.__offset = ui.OFFSETS[player_num]
        self.uiManager = ui_manager
        self.drawer = self.uiManager.drawer

    def missed(self, x, y):
        self.drawer.put_dots([(x, y)], self.__offset)
        self.player.field.cells_state[(x, y)] = False

    def wounded(self, x, y):
        offset_for_field = self.uiManager.field_params.offset
        self.drawer.put_cross(ui.cell_size * (x - 1 + self.__offset +
                                              offset_for_field),
                              ui.cell_size * (y - 1 + offset_for_field) +
                              ui.top_margin)
        self.drawer.put_dots([(x + 1, y + 1), (x - 1, y - 1), (x + 1, y - 1),
                              (x - 1, y + 1)], self.__offset)
        self.player.field.ships[(x, y)] = (True,
                                           self.player.field.ships[(x, y)][1])
        self.player.field.cells_state[(x, y)] = False
        for i in [(x + 1, y + 1), (x - 1, y - 1), (x + 1, y - 1),
                  (x - 1, y + 1)]:
            self.player.field.cells_state[i] = False

    def is_killed(self, x, y):
        killed_ship = [(x, y)]
        for neighbour in self.player.field.ships[(x, y)][1]:
            n_x = neighbour[0]
            n_y = neighbour[1]
            if self.player.field.ships[(n_x, n_y)][0]:
                killed_ship.append((n_x, n_y))
        if len(killed_ship) == len(self.player.field.ships[(x, y)][1]) + 1:
            return True
        return False

    def killed(self, x, y):
        offset_for_field = self.uiManager.field_params.offset
        self.drawer.put_cross(ui.cell_size * (x - 1 + self.__offset +
                                              offset_for_field), ui.cell_size *
                              (y - 1 + offset_for_field) +
                              ui.top_margin, ui.RED)
        self.player.field.cells_state[(x, y)] = False
        neighbours = self.player.field.ships[(x, y)][1]
        for neighbour in neighbours:
            self.drawer.put_cross(ui.cell_size * (neighbour[0] - 1
                                                  + self.__offset +
                                                  offset_for_field),
                                  ui.cell_size *
                                  (neighbour[1] - 1 + offset_for_field) +
                                  ui.top_margin, ui.RED)
            self.player.field.cells_state[neighbour] = False
        dots = []
        ship = [n for n in neighbours]
        ship.append((x, y))
        if len(ship) > 1:
            if ship[0][0] == ship[1][0]:
                ship.sort(key=lambda i: i[1])
                dots = [(ship[0][0], ship[0][1] - 1),
                        (ship[0][0], ship[-1][1] + 1)]
            elif ship[0][1] == ship[1][1]:
                ship.sort(key=lambda i: i[0])
                dots = [(ship[0][0] - 1, ship[0][1]),
                        (ship[-1][0] + 1, ship[0][1])]
        else:
            dots = [(x, y - 1), (x + 1, y), (x, y + 1), (x - 1, y)]
        for dot in dots:
            self.player.field.cells_state[dot] = False
        self.drawer.put_dots(dots, self.__offset)


class Game:
    def __init__(self):
        # объявляем все необходимые для игры переменные
        self.game_start = False
        self.level_chosen = False
        self.field_set_up = False
        self.field_made = False
        self.ships_created = False
        self.bot_turn = False
        self.game_over = False
        self.game_finished = False
        self.game_paused = False

        self.uiManager = UIManager()
        self.labels = {}
        self.players = {}
        self.shootings = {}
        self.level = 0
        self.enemy_num = 2
        self.player_num = 1
        self.ships_to_draw = []
        self.drawn_ships = [0 for _ in range(15)]
        self.scene_number = 0

    def play_game(self):
        self.change_to_choose_mode()

    def change_to_choose_mode(self, go_back=False, delta=1):
        if go_back:
            self.uiManager.go_back(delta)
        else:
            self.uiManager.next_window(0)
        self.game_start = False
        self.choose_mode()

    def change_to_choose_level(self, go_back=False):
        if go_back:
            self.uiManager.go_back()
        else:
            self.uiManager.next_window()
        self.level_chosen = False
        self.choose_level()

    def change_to_setup_field(self, go_back=False, delta=1):
        if go_back:
            self.uiManager.go_back()
        else:
            self.uiManager.next_window(delta)
        self.field_set_up = False
        self.setup_field()

    def change_to_create_field(self, player, go_back=False):
        self.uiManager.create_window.clear_labels()
        self.uiManager.create_window.add_changing_labels(
            ui.Label(self.labels[player], (22 * ui.cell_size, ui.cell_size)))
        self.uiManager.set_ships_in_game()
        if go_back:
            self.uiManager.go_back()
        else:
            self.uiManager.next_window()
        self.field_made = False
        self.ships_created = False
        self.create_field(player)

    def change_to_play_game(self, go_back=False, delta=1):
        if go_back:
            self.uiManager.go_back(delta)
        else:
            self.uiManager.next_window(delta)
        self.game_over = False
        self.game_paused = False
        self.play()

    def change_to_finish(self):
        self.uiManager.next_window()
        self.finish()

    # вызывается когда мы нажимаем на выходи из игры (чтобы в каждом цикле
    # эти переменные не перечислять)
    def quit_game(self):
        self.game_start = True
        self.level_chosen = True
        self.field_set_up = True
        self.field_made = True
        self.bot_turn = True
        self.game_over = True
        self.game_finished = True
        # self.quit_menu = True

    # выбираются подписи к полям в зависимости от режима игры
    def set_labels(self):
        if GAME_WITH_BOT:
            self.labels = {1: 'Ваше поле',
                           2: 'Поле компьютера'}
        else:
            self.labels = {1: 'Игрок 1',
                           2: 'Игрок 2'}

    # создается словарь с игроками в зависимости от режима игры
    def set_players(self):
        if GAME_WITH_BOT:
            self.players = {1: Player(self.uiManager),
                            2: Bot(1, self.uiManager.field_params)}
        else:
            self.players = {1: Player(self.uiManager),
                            2: Player(self.uiManager)}

    # создается словарь с шутинг менеджерами
    def set_shootings(self):
        self.shootings = {1: ShootingManager(1, self.players[1],
                                             self.uiManager),
                          2: ShootingManager(2, self.players[2],
                                             self.uiManager)}

    def set_mode(self, bot):
        global GAME_WITH_BOT
        GAME_WITH_BOT = bot
        self.game_start = True
        self.set_labels()
        self.set_players()
        self.set_shootings()
        if not GAME_WITH_BOT:
            self.change_to_setup_field(delta=2)
        else:
            self.change_to_choose_level()

    # метод для окна с выбором режима игры
    def choose_mode(self):
        while not self.game_start:
            mouse = pygame.mouse.get_pos()
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.quit_game()
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if self.uiManager.start_with_friend_btn.rect. \
                            collidepoint(mouse):
                        self.set_mode(False)
                    elif self.uiManager.start_with_computer_btn.rect. \
                            collidepoint(mouse):
                        self.set_mode(True)
                    elif self.uiManager.sound_btn.rect.collidepoint(mouse):
                        self.uiManager.change_sound_volume()
            pygame.display.update()

    def set_level(self, level):
        labels = {
            1: ui.Label('Лёгкий уровень', (22 * ui.cell_size, ui.cell_size)),
            2: ui.Label('Средний уровень', (22 * ui.cell_size, ui.cell_size)),
            3: ui.Label('Сложный уровень', (22 * ui.cell_size, ui.cell_size))}
        self.level = level
        self.level_chosen = True
        self.uiManager.game_window.add_fixed_labels(labels[level])
        self.change_to_setup_field()

    # метод для окна с выбором уровня бота. открывается,
    # если мы выбрали играть с ботом
    def choose_level(self):
        while not self.level_chosen:
            mouse = pygame.mouse.get_pos()
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.quit_game()
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if self.uiManager.level_1_btn.rect.collidepoint(mouse):
                        self.set_level(1)
                    elif self.uiManager.level_2_btn.rect.collidepoint(mouse):
                        self.set_level(2)
                    elif self.uiManager.level_3_btn.rect.collidepoint(mouse):
                        self.set_level(3)
                    elif self.uiManager.back_btn.rect.collidepoint(mouse):
                        self.level_chosen = True
                        self.change_to_choose_mode(True)
                    elif self.uiManager.sound_btn.rect.collidepoint(mouse):
                        self.uiManager.change_sound_volume()
            pygame.display.update()

    def change_param(self, i, delta):
        self.uiManager.field_params.nums_of_ships[i // 2] += delta
        self.uiManager.field_params.update_params()
        self.uiManager.drawer = DrawManager(self.uiManager.field_params)
        self.uiManager.drawer.put_params_labels()

    # проверяет не нажата ли кнопка + или - в окне с настройками
    # (кроме + и - для раземра поля)
    def check_buttons(self, mouse):
        for i in range(0, len(self.uiManager.plus_minus_buttons) - 1, 2):
            minus_btn, plus_btn = self.uiManager.plus_minus_buttons[i], \
                                  self.uiManager.plus_minus_buttons[i + 1]
            # если кнопка - нажата, уменьшаем количество соответствующих
            # кораблей, обновляем везде параметры
            if minus_btn.rect.collidepoint(mouse):
                if self.uiManager.field_params.nums_of_ships[i // 2] == 0:
                    continue
                self.change_param(i, -1)
            # если кнопка + нажата, увеличиваем количество соответствующих
            # кораблей, обновляем везде параметры
            elif plus_btn.rect.collidepoint(mouse):
                self.change_param(i, 1)

    # проверяет верны ли введеные в настйроках параметры
    def are_params_correct(self):
        return not self.zero_ships() and \
               self.uiManager.field_params.field_size > 0 and \
               not self.too_many_ships()

    # возвращает True, если не выбрано ни одного корабля. Иначе - False
    def zero_ships(self):
        for num in self.uiManager.field_params.nums_of_ships:
            if num != 0:
                return False
        return True

    # возвращает True, если корабли не влезают на поле. Иначе - False
    def too_many_ships(self):
        total = 0
        field_size = self.uiManager.field_params.field_size
        for i in range(len(self.uiManager.field_params.nums_of_ships)):
            ship_length = i + 1
            ship_amount = self.uiManager.field_params.nums_of_ships[i]
            if ship_length == field_size:
                total += ship_length * 2 * ship_amount
            else:
                total += (ship_length * 2 + 2) * ship_amount
        return total > (self.uiManager.field_params.field_size *
                        self.uiManager.field_params.field_size)

    # если мы уменьшили размер поля, но не уменьшили количество кораблей,
    # длина которых больше длины поля, вызывается этот метод, и слишком длинные
    # корабли удаляются
    def delete_extra_ships(self):
        for i in range(self.uiManager.field_params.field_size,
                       len(self.uiManager.field_params.nums_of_ships)):
            if self.uiManager.field_params.nums_of_ships[i] != 0:
                self.uiManager.field_params.nums_of_ships[i] = 0

    def change_size(self, delta):
        self.uiManager.field_params.field_size += delta
        self.uiManager.update_settings_window()
        self.delete_extra_ships()

    # метод для окна с настройками
    def setup_field(self):
        if not self.field_set_up:
            self.uiManager.update_settings_window()
        while not self.field_set_up:
            mouse = pygame.mouse.get_pos()
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.quit_game()
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    # увеличиваем размер поля
                    if self.uiManager.plus_size_btn.rect.collidepoint(mouse) \
                            and self.uiManager.field_params.field_size < 15:
                        self.change_size(1)
                    # уменьшаем размер поля
                    elif self.uiManager.minus_size_btn.rect. \
                            collidepoint(mouse) \
                            and self.uiManager.field_params.field_size > 2:
                        self.change_size(-1)
                    elif self.uiManager.next_btn.rect.collidepoint(mouse):
                        # перед тем как перейти к созданию поля, проверяем
                        # верны ли параметры
                        if self.are_params_correct():
                            self.field_set_up = True
                            self.uiManager.field_params.update_params()
                            for p in self.players.values():
                                p.field.field_size = \
                                    self.uiManager.field_params.field_size
                                p.field.nums_of_ships = \
                                    self.uiManager.field_params.field_size
                                p.field.set_cells_state()
                            self.uiManager.drawer = DrawManager(
                                self.uiManager.field_params)
                            self.change_to_create_field(1)
                        # если не верны, то выводим сообщение о
                        # соответствующей ошибке
                        else:
                            if self.too_many_ships():
                                self.uiManager.drawer.put_error_message(
                                    'Слишком много кораблей')
                            elif self.zero_ships():
                                self.uiManager.drawer.put_error_message(
                                    'Слишком мало кораблей')
                    elif self.uiManager.back_btn.rect.collidepoint(mouse):
                        if GAME_WITH_BOT:
                            self.change_to_choose_level(True)
                        else:
                            self.change_to_choose_mode(True, 2)
                    elif self.uiManager.sound_btn.rect.collidepoint(mouse):
                        self.uiManager.change_sound_volume()
                    else:
                        # проверяем кнопки + и -
                        self.check_buttons(mouse)
            pygame.display.update()

    # перерисовывает поле, удаляет с него все корабли
    def clear_field(self, num):
        self.uiManager.next_window(0)
        self.players[num].field.set_cells_state()
        self.players[num].field.ships = dict()
        self.ships_to_draw = []
        self.drawn_ships = [0 for _ in range(15)]
        self.field_made = False
        self.ships_created = False

    def set_start_end_cells(self, x_end, x_start, y_start, y_end):
        offset_for_field = self.uiManager.field_params.offset
        middle_offset = ui.middle_offset
        start_cell = (int(x_start / ui.cell_size
                          + 1 - offset_for_field - middle_offset),
                      int((y_start - ui.top_margin) / ui.cell_size
                          + 1 - offset_for_field))
        end_cell = (int(x_end / ui.cell_size
                        + 1 - offset_for_field - middle_offset),
                    int((y_end - ui.top_margin) / ui.cell_size
                        + 1 - offset_for_field))
        if start_cell > end_cell:
            start_cell, end_cell = end_cell, start_cell
        return start_cell, end_cell

    def check_borders(self, start_cell, end_cell, ships_stop_list, temp_ship,
                      player):
        # проверяем, что не зашли за границы поля
        turn = 0
        size = self.uiManager.field_params.field_size
        if 1 <= start_cell[0] <= size and 1 <= start_cell[1] <= size \
                and 1 <= end_cell[0] <= size and 1 <= end_cell[1] <= size:

            if end_cell[0] - start_cell[0] + 1 in ships_stop_list \
                    and end_cell[1] - start_cell[1] + 1 in \
                    ships_stop_list:
                return
            else:
                if start_cell[0] == end_cell[0]:
                    turn = 0
                    for cell in range(start_cell[1],
                                      end_cell[1] + 1):
                        temp_ship.append((start_cell[0], cell))

                elif start_cell[1] == end_cell[1]:
                    turn = 1
                    for cell in range(start_cell[0],
                                      end_cell[0] + 1):
                        temp_ship.append((cell, start_cell[1]))

        if temp_ship and \
                self.players[player].field.is_ship_can_be_put(
                    temp_ship) and \
                self.drawn_ships[len(temp_ship) - 1] < \
                self.uiManager.field_params.nums_of_ships[
                    len(temp_ship) - 1]:
            self.players[player].field.add_ship(temp_ship, turn)
            self.drawn_ships[len(temp_ship) - 1] += 1
            self.ships_to_draw.append((temp_ship, turn))

    # метод для окна с созданием поля
    def create_field(self, player):
        can_draw = False
        drawing = False
        x_start, y_start = 0, 0
        ship_size = 0, 0
        self.clear_field(player)
        # создаем и заполняем список с номерами кораблей, которых нет в игре
        ships_stop_list = []
        for n in range(len(
                self.uiManager.field_params.nums_of_ships)):
            if self.uiManager.field_params.nums_of_ships[n] == 0:
                ships_stop_list.append(n + 1)

        while not self.field_made:
            mouse = pygame.mouse.get_pos()
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.quit_game()
                # если нажата кнопка 'дальше'
                elif event.type == pygame.MOUSEBUTTONDOWN \
                        and self.uiManager.next_btn.rect.collidepoint(mouse) \
                        and self.ships_created:
                    self.field_made = True
                    if player == 1:
                        if GAME_WITH_BOT:
                            self.players[2].field.generate_ships(
                                self.uiManager)
                            self.change_to_play_game(delta=2)
                        else:
                            self.change_to_create_field(2)
                    else:
                        self.change_to_play_game()

                elif event.type == pygame.MOUSEBUTTONDOWN and \
                        self.uiManager.sound_btn.rect.collidepoint(
                        mouse):
                    self.uiManager.change_sound_volume()

                elif event.type == pygame.MOUSEBUTTONDOWN and \
                        self.uiManager.back_btn.rect.collidepoint(
                        mouse):
                    self.field_made = True
                    if player == 2:
                        self.change_to_create_field(1, True)
                    else:
                        self.change_to_setup_field(True)

                # если нажата кнопка 'сгенерировать рандомно'
                elif event.type == pygame.MOUSEBUTTONDOWN \
                        and self.uiManager.random_btn.rect.collidepoint(mouse):
                    # если мы уже порисовали, то поле отчищается
                    if can_draw:
                        can_draw = False
                        self.clear_field(player)
                    # и генерируется новое
                    self.players[player].field.generate_ships(self.uiManager)
                    self.uiManager.drawer.update_ships_in_game(
                        self.uiManager.field_params.nums_of_ships)
                    self.ships_created = True
                # если нажата кнопка 'стереть всё', поле отчищается
                elif event.type == pygame.MOUSEBUTTONDOWN \
                        and self.uiManager.clear_btn.rect.collidepoint(mouse):
                    self.clear_field(player)
                # если нажата кнопка 'отмена', стирается последний
                # нарисованный корабль
                elif event.type == pygame.MOUSEBUTTONDOWN \
                        and self.uiManager.cancel_btn.rect.collidepoint(mouse)\
                        and can_draw:
                    if self.ships_to_draw:
                        last_ship = self.ships_to_draw.pop()
                        self.drawn_ships[len(last_ship[0]) - 1] -= 1
                        self.players[player].field.remove_ship(last_ship)
                # если нажата кнопка 'нарисовать', можем начать рисовать
                elif event.type == pygame.MOUSEBUTTONDOWN and \
                        self.uiManager.manual_btn.rect.collidepoint(mouse):
                    can_draw = True
                    self.clear_field(player)

                # далее процесс рисования
                # отмечаем куда мы нажали мышкой, то есть начало корабля
                elif event.type == pygame.MOUSEBUTTONDOWN and can_draw:
                    drawing = True
                    x_start, y_start = event.pos
                    ship_size = 0, 0
                # ведём мышкой
                elif event.type == pygame.MOUSEMOTION and drawing:
                    x_end, y_end = event.pos
                    ship_size = x_end - x_start, y_end - y_start
                # заканичваем корабль
                elif event.type == pygame.MOUSEBUTTONUP and drawing:
                    x_end, y_end = event.pos
                    ship_size = 0, 0
                    drawing = False
                    start_cell, end_cell = self.set_start_end_cells(x_end,
                                                                    x_start,
                                                                    y_start,
                                                                    y_end)
                    temp_ship = []
                    # проверяем, что не зашли за границы поля
                    self.check_borders(start_cell, end_cell, ships_stop_list,
                                       temp_ship, player)

                # проверяем что нарисовали уже все корабли
                if len(self.ships_to_draw) == self.uiManager.field_params.\
                        total_amount_of_ships:
                    self.ships_created = True
            # если поле еще не создано и мы в процессе рисования, отрисовываем
            # нарисованные корабли
            if not self.field_made and can_draw:
                self.uiManager.drawer.show_window(self.uiManager.create_window)
                pygame.draw.rect(ui.screen, ui.BUTTON_BLUE,
                                 ((x_start, y_start), ship_size), 3)
                for ship, turn in self.ships_to_draw:
                    self.uiManager.drawer.update_ships_in_game(
                        self.drawn_ships)
                    self.uiManager.drawer.draw_ship(ship, turn)
            pygame.display.update()

    # передается ход
    def change_turn(self):
        self.uiManager.drawer.update_turn(self.labels[self.player_num],
                                          self.labels[self.enemy_num])
        self.player_num, self.enemy_num = self.enemy_num, self.player_num
        if GAME_WITH_BOT:
            self.bot_turn = not self.bot_turn

    # возвращает True, если текущий игрок стал победителем
    def is_winner(self):
        return self.players[self.player_num].score == \
               self.uiManager.field_params.max_score

    def find_winner(self):
        if self.players[1].score > self.players[2].score:
            return 1
        elif self.players[2].score > self.players[1].score:
            return 2
        elif self.players[1].score == self.players[2].score:
            return 0

    def kill(self, fired_cell):
        if self.bot_turn:
            self.players[2].killed = True
        self.shootings[self.enemy_num].killed(fired_cell[0],
                                              fired_cell[1])
        ui.sound_killed.play()

        self.uiManager.drawer.last_move(fired_cell, 'убил', self.player_num)

    def wound(self, fired_cell):
        # у бота отмечаем что мы еще не убили корабль полностью
        if self.bot_turn:
            self.players[2].killed = False
        # "раним" клетку
        self.shootings[self.enemy_num].wounded(fired_cell[0],
                                               fired_cell[1])
        ui.sound_wounded.play()
        self.uiManager.drawer.last_move(fired_cell, 'ранил', self.player_num)

    def win(self):
        self.game_over = True
        winner = self.find_winner()

        if winner == 0:
            self.uiManager.win_window.add_fixed_labels(
                ui.Label('Ничья', (ui.screen_width / 2, 2 * ui.cell_size)))
        else:
            score_label = ui.Label(
                'со счётом: {0}'.format(
                    self.players[winner].score),
                (ui.screen_width / 2, 4 * ui.cell_size))

            if GAME_WITH_BOT:
                if winner == 1:
                    self.uiManager.win_window.add_fixed_labels(
                        ui.Label('Вы победили',
                                 (ui.screen_width / 2, 2 * ui.cell_size)),
                        score_label)
                else:
                    self.uiManager.win_window.add_fixed_labels(
                        ui.Label('Компьютер победил', (
                            ui.screen_width / 2, 2 * ui.cell_size)),
                        score_label)
            else:
                self.uiManager.win_window.add_fixed_labels(
                    ui.Label('Игрок {0} победил'.format(winner),
                             (ui.screen_width / 2, 2 * ui.cell_size)),
                    ui.Label(
                        'со счётом: {0}'.format(
                            self.players[winner].score),
                        (ui.screen_width / 2, 4 * ui.cell_size)))
        self.change_to_finish()

    def miss(self, fired_cell):
        self.change_turn()
        self.shootings[self.player_num].missed(fired_cell[0],
                                               fired_cell[1])
        ui.sound_missed.play()
        self.uiManager.drawer.last_move(fired_cell, 'мимо', self.player_num)

    def check_fired_cell(self, fired_cell, enemy):
        if fired_cell != (0, 0) and \
                fired_cell[0] != self.uiManager.field_params.field_size + 1:
            # если попали в корабль врага и он еще не подбитый
            if fired_cell in enemy.field.ships and \
                    enemy.field.ships[fired_cell][0] is False:
                # если стрелял бот, то отмечаем, что это был удачный выстрел
                if self.bot_turn:
                    self.players[2].last_good_shot = fired_cell
                # делаем клетку недоступной. в нее больше нельзя стрелять
                enemy.field.cells_state[fired_cell] = False
                # увеличиваем очки
                self.players[self.player_num].score += 1
                # обновляем лейбл с очками
                self.uiManager.drawer.update_score(
                    self.players[self.player_num].score,
                    self.player_num)
                self.shootings[self.enemy_num].wounded(fired_cell[0],
                                                       fired_cell[1])

                # если убили корабль
                if self.shootings[self.enemy_num].is_killed(fired_cell[0],
                                                            fired_cell[1]):
                    self.kill(fired_cell)
                else:
                    self.wound(fired_cell)

                if self.is_winner():
                    self.win()

            elif fired_cell not in enemy.field.ships and \
                    enemy.field.cells_state[fired_cell] is True:
                self.miss(fired_cell)

    # метод для окна игры
    def play(self):
        self.uiManager.drawer.update_score(0, 1)
        self.uiManager.drawer.update_score(0, 2)
        self.uiManager.drawer.update_turn(self.labels[self.enemy_num],
                                          self.labels[self.player_num], False)

        for p in self.players.values():
            p.field.set_cells_state()
            for k, v in p.field.ships.items():
                p.field.ships[k] = (False, p.field.ships[k][1])
            p.score = 0

        while not self.game_over:
            mouse = pygame.mouse.get_pos()
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.quit_game()
                elif event.type == pygame.MOUSEBUTTONDOWN and \
                        self.uiManager.menu_btn.rect.collidepoint(
                            mouse) and not self.game_paused:
                    self.uiManager.drawer.show_menu(
                        self.uiManager.menu_buttons)
                    self.game_paused = True
                elif event.type == pygame.MOUSEBUTTONDOWN and \
                        self.uiManager.sound_btn.rect.collidepoint(
                        mouse):
                    self.uiManager.change_sound_volume()
                elif (event.type == pygame.MOUSEBUTTONDOWN or self.bot_turn) \
                        and not self.game_paused:
                    enemy = self.players[self.enemy_num]
                    if self.bot_turn:
                        fired_cell = self.players[2].do_shot(enemy, self.level)
                    else:
                        fired_cell = self.players[self.player_num].do_shot(
                            event, ui.OFFSETS[self.enemy_num])
                    self.check_fired_cell(fired_cell, enemy)
                elif self.game_paused and event.type == pygame.MOUSEBUTTONDOWN:
                    if self.uiManager.continue_btn.rect.collidepoint(mouse):
                        self.uiManager.drawer.hide_menu(
                            self.uiManager.menu_buttons)
                        self.game_paused = False
                    elif self.uiManager.restart_btn.rect.collidepoint(mouse):
                        self.game_over = True
                        self.uiManager.drawer.hide_menu(
                            self.uiManager.menu_buttons)
                        self.change_to_play_game(True, 0)
                    elif self.uiManager.surrender_btn.rect.collidepoint(mouse):
                        self.game_over = True
                        self.win()
                    elif self.uiManager.main_nenu_btn.rect.collidepoint(mouse):
                        self.game_over = True
                        self.player_num, self.enemy_num = 1, 2
                        self.change_to_choose_mode(True, 5)

            pygame.display.update()

    # метод для окна победы
    def finish(self):
        while not self.game_finished:
            mouse = pygame.mouse.get_pos()
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.quit_game()
                # начинаем заново
                elif event.type == pygame.MOUSEBUTTONDOWN and \
                        self.uiManager.restart_btn.rect.collidepoint(mouse):
                    self.game_finished = True
                    game = Game()
                    game.play_game()
            pygame.display.update()


def main():
    game = Game()
    game.play_game()


if __name__ == '__main__':
    main()
    pygame.quit()

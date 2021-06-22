import pygame

BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
RED = (255, 0, 0)
LIGHT_BLUE = (65, 105, 225)
BLUE = (0, 0, 139)
BUTTON_BLUE = (70, 130, 180)
SKY_BLUE = (193, 227, 255)
DARK_BLUE = (21, 63, 101)
cell_size = 30
left_margin = 60
top_margin = 90
screen_width, screen_height = left_margin * 2 + cell_size * 40, \
                              top_margin * 2 + cell_size * 17
btn_width, btn_height = 210, 60

OFFSETS = {1: 3,
           2: 27}

middle_offset = (screen_width - 15 * cell_size) / 2 / cell_size  # отступ для
# рисования поля посередине

pygame.init()

screen = pygame.display.set_mode((screen_width, screen_height))
pygame.display.set_caption('Морской бой')

font_size = 15
font = pygame.font.Font('fonts/Azov.ttf', font_size)

pygame.mixer.music.load('audio/morskoj-priboj.ogg')
sound_missed = pygame.mixer.Sound('audio/splash.ogg')
sound_wounded = pygame.mixer.Sound('audio/shot.ogg')
sound_killed = pygame.mixer.Sound('audio/killed-shot.ogg')


class FieldParams:
    def __init__(self):
        self.field_size = 10
        self.nums_of_ships = [4, 3, 2, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
        # индекс + 1 - длина корабля, значение - количество таких кораблей
        self.total_amount_of_ships = 10
        self.max_score = 20
        self.offset = (15 - self.field_size) / 2  # отступ для того,
        # чтобы корабли всех размеров отрисовывались одинаково по центру

    def update_params(self):
        self.total_amount_of_ships = sum(self.nums_of_ships)
        self.max_score = sum(self.nums_of_ships[i] * (i + 1) for i in
                             range(len(self.nums_of_ships)))
        self.offset = (15 - self.field_size) / 2


class Button:
    def __init__(self, button_title, params, width=btn_width,
                 height=btn_height):
        self.title = button_title
        self.title_width, self.title_height = font.size(self.title)
        self.x_start, self.y_start = params[0], params[1]
        self.width, self.height = width, height
        self.rect = pygame.Rect((self.x_start, self.y_start,
                                 width, height))


class ImageButton(Button):
    def __init__(self, image):
        super().__init__('', (cell_size, cell_size), 2 * cell_size,
                         2 * cell_size)
        self.image = pygame.image.load(image)
        self.image = pygame.transform.scale(self.image, (2 * cell_size,
                                                         2 * cell_size))
        self.image.set_colorkey(WHITE)
        self.rect = pygame.Rect(cell_size, cell_size, 2 * cell_size,
                                2 * cell_size)


class Label:
    def __init__(self, text, params, color=DARK_BLUE, label_font=font):
        self.text = label_font.render(text, True, color)
        self.width, self.height = font.size(text)
        self.x_start, self.y_start = params[0], params[1]


class Window:
    # класс окна хранит в себе список кнопок, лейблов и количетсво полей,
    # которые он в себе содержит. это удобно при отрисовывании окна
    def __init__(self):
        self.fields = 0
        self.fixed_buttons = []
        self.fixed_labels = []
        self.changing_labels = []
        self.changing_buttons = []
        self.sound_button = ImageButton('pictures/sound.png')

    def add_fixed_buttons(self, *buttons):
        self.fixed_buttons = [button for button in buttons]

    def add_fixed_labels(self, *labels):
        self.fixed_labels = [label for label in labels]

    def add_changing_labels(self, *labels):
        for label in labels:
            self.changing_labels.append(label)

    def add_changing_buttons(self, *buttons):
        for button in buttons:
            self.changing_buttons.append(button)

    def clear_buttons(self):
        self.changing_buttons = []

    def clear_labels(self):
        self.changing_labels = []


class UIManager:
    # тут создаются и хранятся все кнопки и окна. лейблы как переменные не
    # хранятся.
    def __init__(self):
        self.sound_btn = ImageButton('pictures/sound.png')
        self.plus_minus_buttons = []
        self.win_window = Window()
        self.game_window = Window()
        self.create_window = Window()
        self.settings_window = Window()
        self.levels_window = Window()
        self.start_window = Window()
        self.field_params = FieldParams()
        self.drawer = DrawManager(self.field_params)
        self.create_buttons()
        self.set_windows()
        self.windows_order = {
            0: self.start_window,
            1: self.levels_window,
            2: self.settings_window,
            3: self.create_window,
            4: self.create_window,
            5: self.game_window,
            6: self.win_window
        }
        self.window_number = 0
        self.menu_buttons = [self.continue_btn, self.restart_btn,
                             self.surrender_btn, self.main_nenu_btn]
        self.sound_on = False
        self.change_sound_volume()

    # координаты полежения кнопок с плюсами минусами в окне настроек зависят
    # от размера поля, поэтому при изменении размера поля их нужно
    # пересоздавать. это делает этот метод
    def set_plus_minus_buttons(self):
        self.plus_minus_buttons = []
        size = self.field_params.field_size
        x_start = left_margin + (size + 1) * cell_size
        y_start = 5 * cell_size
        if size % 2 == 0:
            middle = size // 2
        else:
            middle = size // 2 + 1
        start, end = 0, middle
        for j in range(2):
            for i in range(start, end):
                minus_btn = Button('-', (x_start, y_start), cell_size,
                                   cell_size)
                plus_btn = Button('+', (x_start + 3 * cell_size, y_start),
                                  cell_size, cell_size)
                self.plus_minus_buttons.append(minus_btn)
                self.plus_minus_buttons.append(plus_btn)
                y_start += 2 * cell_size

            x_start += 21 * cell_size
            y_start = 5 * cell_size
            start, end = middle, size

    def create_buttons(self):
        y_start = (screen_height - 2 * btn_height - cell_size) / 2
        self.start_with_friend_btn = Button(
            'Играть с другом', ((screen_width - btn_width) / 2, y_start))
        self.start_with_computer_btn = Button(
            'Играть с компьютером', ((screen_width - btn_width) / 2,
                                     y_start + btn_height + cell_size))
        y_start = (screen_height - 3 * btn_height - 2 * cell_size) / 2
        self.level_1_btn = Button(
            'Лёгкий уровень', ((screen_width - btn_width) / 2, y_start))
        self.level_2_btn = Button(
            'Средний уровень', ((screen_width - btn_width) / 2,
                                y_start + btn_height + cell_size))
        self.level_3_btn = Button(
            'Сложный уровень', ((screen_width - btn_width) / 2,
                                y_start + 2 * btn_height + 2 * cell_size))
        y_start = (screen_height - 4 * btn_height - 3 * cell_size) / 2
        self.continue_btn = Button(
            'Продолжить', ((screen_width - btn_width) / 2, y_start))
        self.restart_btn = Button(
            'Начать заново', ((screen_width - btn_width) / 2, y_start +
                              btn_height + cell_size))
        self.surrender_btn = Button(
            'Сдаться', ((screen_width - btn_width) / 2, y_start + 2 *
                        btn_height + 2 * cell_size))
        self.main_nenu_btn = Button(
            'Выйти в главное меню', ((screen_width - btn_width) / 2,
                                     y_start + 3 * btn_height + 3 * cell_size))
        self.menu_btn = Button(
            'Меню', (screen_width - 3 * cell_size, cell_size),
            2 * cell_size, cell_size)
        self.next_btn = Button(
            'Дальше', (screen_width - left_margin - btn_width,
                       screen_height - 3 * cell_size))
        self.back_btn = Button(
            'Назад', (left_margin, screen_height - 3 * cell_size))
        self.random_btn = Button(
            'Расставить рандомно', (screen_width - left_margin - btn_width,
                                    top_margin + 1.5 * btn_height))
        self.manual_btn = Button(
            'Нарисовать', (screen_width - left_margin - btn_width, top_margin))
        self.clear_btn = Button(
            'Стереть всё', (screen_width - left_margin - btn_width,
                            top_margin + 4.5 * btn_height))
        self.cancel_btn = Button(
            'Отмена', (screen_width - left_margin - btn_width,
                       top_margin + 3 * btn_height))
        self.plus_size_btn = Button(
            '+', (left_margin + 23 * cell_size, 3 * cell_size),
            cell_size, cell_size)
        self.minus_size_btn = Button(
            '-', (left_margin + 20 * cell_size, 3 * cell_size),
            cell_size, cell_size)
        self.set_plus_minus_buttons()

    def set_windows(self):
        self.start_window.add_fixed_buttons(self.start_with_friend_btn,
                                            self.start_with_computer_btn)
        self.start_window.add_fixed_labels(Label(
            'Морской бой', (screen_width // 2 - 1.5 * cell_size,
                            3 * cell_size), label_font=pygame.font.Font(
                'fonts/Azov.ttf', 30)))

        self.levels_window.add_fixed_buttons(
            self.level_1_btn, self.level_2_btn, self.level_3_btn,
            self.back_btn)
        self.levels_window.add_fixed_labels(Label(
            'Выберите уровень сложности', (screen_width / 2, top_margin)))

        self.settings_window.add_fixed_buttons(self.plus_size_btn,
                                               self.minus_size_btn,
                                               self.next_btn, self.back_btn)
        self.settings_window.add_fixed_labels(
            Label('Настройте параметры поля', (screen_width / 2, cell_size)),
            Label('Размер поля', (left_margin + 17 * cell_size,
                                  3 * cell_size)))
        for button in self.plus_minus_buttons:
            self.settings_window.add_changing_buttons(button)

        self.create_window.add_fixed_buttons(self.next_btn, self.random_btn,
                                             self.manual_btn, self.cancel_btn,
                                             self.clear_btn, self.back_btn)
        self.create_window.add_fixed_labels(
            Label('Доступные корабли', (7 * cell_size, 3 * cell_size)),
            Label('Размер', (5 * cell_size, 4 * cell_size)),
            Label('Количество', (9 * cell_size, 4 * cell_size)))
        self.create_window.fields = 1

        self.game_window.add_fixed_buttons(self.menu_btn)
        self.game_window.fields = 2

        self.win_window.add_fixed_buttons(self.restart_btn)

    def next_window(self, delta=1):
        self.window_number += delta
        self.drawer.show_window(self.windows_order[self.window_number])

    def go_back(self, delta=1):
        self.window_number -= delta
        self.drawer.show_window(self.windows_order[self.window_number])

    def change_sound_volume(self):
        if self.sound_on:
            self.sound_on = False
            pygame.mixer.music.set_volume(0)
            sound_missed.set_volume(0)
            sound_wounded.set_volume(0)
            sound_killed.set_volume(0)
            self.sound_btn = ImageButton('pictures/crossed_sound.png')
        else:
            self.sound_on = True
            pygame.mixer.music.set_volume(0.3)
            pygame.mixer.music.play(loops=-1)
            sound_missed.set_volume(0.8)
            sound_wounded.set_volume(2)
            sound_killed.set_volume(1.3)
            self.sound_btn = ImageButton('pictures/sound.png')
        pygame.draw.rect(screen, WHITE, (cell_size, cell_size, 2 * cell_size,
                                         2 * cell_size))
        for i in range(2):
            pygame.draw.line(screen, SKY_BLUE,
                             (cell_size, cell_size + i * cell_size),
                             (3 * cell_size, cell_size + i * cell_size))
            pygame.draw.line(screen, SKY_BLUE,
                             (cell_size + i * cell_size, cell_size),
                             (cell_size + i * cell_size, 3 * cell_size))
        screen.blit(self.sound_btn.image, self.sound_btn.rect)
        for window in self.windows_order.values():
            window.sound_button = self.sound_btn

    # обновляет окно с настройками, после того, как меняется рзамер поля
    def update_settings_window(self):
        self.set_plus_minus_buttons()
        self.settings_window.clear_buttons()
        for button in self.plus_minus_buttons:
            self.settings_window.add_changing_buttons(button)
        self.next_window(0)
        self.drawer.draw_ship_examples()
        self.drawer.put_params_labels()

    def set_ships_in_game(self):
        x_start = 5 * cell_size
        y_start = 5 * cell_size
        for i in range(len(self.field_params.nums_of_ships)):
            if self.field_params.nums_of_ships[i] != 0:
                self.create_window.add_changing_labels(
                    Label('{0}'.format(i + 1), (x_start, y_start)))

                y_start += cell_size


class DrawManager:
    def __init__(self, field_params):
        self.field_params = field_params
        self.x_player, self.y_player = \
            (OFFSETS[1] + self.field_params.field_size / 2 +
             self.field_params.offset) * cell_size, cell_size
        self.x_enemy, self.y_enemy = \
            (OFFSETS[2] + self.field_params.field_size / 2 +
             self.field_params.offset) * cell_size, cell_size

    # отображает окно
    def show_window(self, window):
        screen.fill(WHITE)
        self.draw_grid(SKY_BLUE)
        screen.blit(window.sound_button.image, window.sound_button.rect)
        for button in window.fixed_buttons:
            self.draw_button(button)
        for button in window.changing_buttons:
            self.draw_button(button)
        for label in window.fixed_labels:
            self.put_static_label(label)
        for label in window.changing_labels:
            self.put_static_label(label)
        if window.fields == 1:
            self.draw_field(middle_offset)
            self.set_ships_in_game()
        elif window.fields == 2:
            self.draw_field(OFFSETS[1])
            self.draw_field(OFFSETS[2])

    def set_ships_in_game(self):
        x_start = 8 * cell_size
        y_start = 5 * cell_size
        for i in range(len(self.field_params.nums_of_ships)):
            if self.field_params.nums_of_ships[i] != 0:
                pygame.draw.rect(screen, WHITE, (x_start, y_start, 2 *
                                                 cell_size, cell_size))
                pygame.draw.rect(screen, SKY_BLUE,
                                 (x_start, y_start, 2 * cell_size, cell_size),
                                 1)
                pygame.draw.line(screen, SKY_BLUE,
                                 (x_start + cell_size, y_start),
                                 (x_start + cell_size, y_start + cell_size))
                self.put_static_label(Label(str(
                    self.field_params.nums_of_ships[i]),
                    (x_start + cell_size, y_start)))
                y_start += cell_size

    def update_ships_in_game(self, drawn_ships):
        x_start = 8 * cell_size
        y_start = 5 * cell_size
        for i in range(len(self.field_params.nums_of_ships)):
            if self.field_params.nums_of_ships[i] != 0:
                pygame.draw.rect(screen, WHITE, (x_start, y_start, 2 *
                                                 cell_size, cell_size))
                pygame.draw.rect(screen, SKY_BLUE,
                                 (x_start, y_start, 2 * cell_size, cell_size),
                                 1)
                pygame.draw.line(screen, SKY_BLUE,
                                 (x_start + cell_size, y_start),
                                 (x_start + cell_size, y_start + cell_size))
                self.put_static_label(
                    Label(str(self.field_params.nums_of_ships[i] -
                              drawn_ships[i]), (x_start + cell_size, y_start)))
                y_start += cell_size

    def show_menu(self, menu_buttons):
        for btn in menu_buttons:
            self.draw_button(btn)

    @staticmethod
    def hide_menu(menu_buttons):
        for btn in menu_buttons:
            pygame.draw.rect(screen, WHITE, (btn.x_start - 0.5 * cell_size, btn.y_start,
                                             btn.width + cell_size, btn.height))
            for i in range(2):
                pygame.draw.line(screen, SKY_BLUE,
                                 (btn.x_start - 0.5 * cell_size, btn.y_start + i * cell_size),
                                 (btn.x_start + btn_width + cell_size, btn.y_start + i *
                                  cell_size))
            for i in range(btn.width // cell_size + 1):
                pygame.draw.line(screen, SKY_BLUE,
                                 (btn.x_start + (i - 0.5) * cell_size, btn.y_start),
                                 (btn.x_start + (i - 0.5) * cell_size, btn.y_start +
                                  btn.height))

    # рисует сетку на фоне
    @staticmethod
    def draw_grid(color):
        for i in range(screen_width // cell_size):
            pygame.draw.line(screen, color,
                             (cell_size * i, 0),
                             (cell_size * i, screen_height))
            pygame.draw.line(screen, color, (0, cell_size * i),
                             (screen_width, cell_size * i))

    @staticmethod
    def draw_button(button, color=BUTTON_BLUE):
        x_start, y_start = button.x_start, button.y_start
        width, height = button.width, button.height
        title_params = (x_start + width / 2 - button.title_width / 2,
                        y_start + height / 2 - button.title_height / 2)
        pygame.draw.rect(screen, color, (x_start, y_start, width, height))
        screen.blit(font.render(button.title, True, WHITE),
                    title_params)
        button.rect = pygame.Rect((x_start, y_start, width, height))

    # просто пишет текст
    @staticmethod
    def put_static_label(label):
        screen.blit(label.text, (label.x_start - label.width / 2,
                                 label.y_start + 0.25 * cell_size))

    # для надписей которые меняются во время игры (сообщения об ошибках, очки,
    # промазал/убил/ранил).
    def put_dynamic_label(self, label, color=BUTTON_BLUE):
        pygame.draw.rect(screen, color, (label.x_start - label.width / 2 -
                                         cell_size, label.y_start,
                                         label.width + 2 * cell_size,
                                         cell_size))
        self.put_static_label(label)

    def put_error_message(self, message):
        self.put_dynamic_label(Label(message, (22 * cell_size, screen_height -
                                               2 * cell_size), RED))

    # отрисовывает показатели параметров в поле с настройками
    # (которые между кнопочками)
    def put_params_labels(self):
        self.update_param(-1, left_margin + 21 * cell_size, 3 * cell_size)

        x_start = left_margin + (self.field_params.field_size + 2) * cell_size
        y_start = 5 * cell_size
        if self.field_params.field_size % 2 == 0:
            middle = self.field_params.field_size // 2
        else:
            middle = self.field_params.field_size // 2 + 1

        start, end = 0, middle
        for j in range(2):
            for i in range(start, end):
                self.update_param(i, x_start, y_start)
                y_start += 2 * cell_size
            x_start += 21 * cell_size
            y_start = 5 * cell_size
            start, end = middle, self.field_params.field_size

    # вызывается из предыдущего метода. конкретон отрисовывает один параметр
    def update_param(self, ship_num, x_start, y_start):
        pygame.draw.rect(screen, WHITE, (x_start, y_start, 2 *
                                         cell_size, cell_size))
        pygame.draw.rect(screen, SKY_BLUE,
                         (x_start, y_start, 2 * cell_size, cell_size),
                         1)
        pygame.draw.line(screen, SKY_BLUE,
                         (x_start + cell_size, y_start),
                         (x_start + cell_size, y_start + cell_size))
        if ship_num == -1:
            self.put_static_label(Label(str(self.field_params.field_size),
                                        (x_start + cell_size, y_start),
                                        DARK_BLUE))
        else:
            self.put_static_label(Label(str(self.field_params.nums_of_ships
                                            [ship_num]),
                                        (x_start + cell_size, y_start),
                                        DARK_BLUE))

    def update_turn(self, player_label, enemy_label, change=True):
        if change:
            self.x_player, self.x_enemy = self.x_enemy, self.x_player
            self.y_player, self.y_enemy = self.y_enemy, self.y_player
        self.put_dynamic_label(Label(enemy_label,
                                     (self.x_player, self.y_player), WHITE))
        self.put_dynamic_label(Label(player_label,
                                     (self.x_enemy, self.y_enemy), DARK_BLUE),
                               WHITE)

    def last_move(self, fired_cell, damage, player_num):
        letters = ['А', 'Б', 'В', 'Г', 'Д', 'Е', 'Ж', 'З', 'И', 'К', 'Л', 'М',
                   'Н', 'О', 'П']
        let, num = letters[fired_cell[0] - 1], fired_cell[1]
        self.put_dynamic_label(Label(
            '({0}, {1}) - {2}'.format(let, num, damage),
            ((OFFSETS[player_num] + self.field_params.field_size / 2 +
              self.field_params.offset) * cell_size, screen_height - 4 *
             cell_size)), WHITE)

    # рисует корабли в окне настроек
    def draw_ship_examples(self):
        y_start = 5 * cell_size
        x_start = left_margin

        if self.field_params.field_size % 2 == 0:
            middle = self.field_params.field_size // 2
        else:
            middle = self.field_params.field_size // 2 + 1

        start, end = 1, middle + 1
        for x in range(2):
            for i in range(start, end):
                j = 0
                for j in range(i + 1):
                    pygame.draw.line(screen, DARK_BLUE,
                                     (x_start + j * cell_size, y_start),
                                     (x_start + j * cell_size,
                                      y_start + cell_size), 2)
                pygame.draw.line(screen, DARK_BLUE, (x_start, y_start),
                                 (x_start + j * cell_size, y_start), 2)
                pygame.draw.line(screen, DARK_BLUE,
                                 (x_start, y_start + cell_size),
                                 (x_start + j * cell_size, y_start +
                                  cell_size), 2)
                self.put_static_label(Label(str(i), (x_start + 0.5 * cell_size,
                                                     y_start)))
                y_start += 2 * cell_size

            start, end = middle + 1, self.field_params.field_size + 1
            y_start = 5 * cell_size
            x_start += 21 * cell_size

    # рисует поле
    def draw_field(self, offset):
        letters = ['А', 'Б', 'В', 'Г', 'Д', 'Е', 'Ж', 'З', 'И', 'К', 'Л', 'М',
                   'Н', 'О', 'П']
        x_start = (offset + self.field_params.offset) * cell_size
        y_start = top_margin + self.field_params.offset * cell_size
        pygame.draw.rect(screen, WHITE,
                         (x_start, y_start, self.field_params.field_size *
                          cell_size, self.field_params.field_size * cell_size))
        for i in range(self.field_params.field_size + 1):
            # горизонтальные линии
            pygame.draw.line(screen, DARK_BLUE,
                             (x_start, y_start + i * cell_size),
                             (x_start + self.field_params.field_size *
                              cell_size, y_start + i * cell_size), 2)
            # вертикальные линии
            pygame.draw.line(screen, DARK_BLUE,
                             (x_start + i * cell_size, y_start),
                             (x_start + i * cell_size, y_start +
                              self.field_params.field_size * cell_size), 2)

            if i < self.field_params.field_size:
                num = font.render(str(i + 1), True, DARK_BLUE)
                let = font.render(letters[i], True, DARK_BLUE)

                num_width = num.get_width()
                num_height = num.get_height()
                let_width = let.get_width()

                screen.blit(num, (x_start - (cell_size // 2 + num_width // 2),
                                  y_start + i * cell_size + (cell_size // 2 -
                                                             num_height // 2)))

                screen.blit(let, (x_start + i * cell_size +
                                  (cell_size // 2 - let_width // 2),
                                  y_start - num_height * 1.5))

    # рисует один корабль по заданным координатам, повороту
    # (горизонательно, вертикально). вызывается из метода
    # генерирования кораблей
    def draw_ship(self, ship, turn):
        offset = middle_offset
        ship.sort(key=lambda i: i[1])
        x = cell_size * (ship[0][0] - 1) + \
            (offset + self.field_params.offset) * cell_size
        y = cell_size * (ship[0][
                             1] - 1) + top_margin + \
            self.field_params.offset * cell_size
        if turn == 0:
            width = cell_size
            height = cell_size * len(ship)
        else:
            width = cell_size * len(ship)
            height = cell_size
        pygame.draw.rect(screen, BUTTON_BLUE, (x, y, width, height))
        # pygame.draw.sound_rect(screen, BLUE, ((x, y), (width, height)),
        #                  width=cell_size // 10)

    # обновляет лейб с очками
    def update_score(self, score, player_num):
        self.put_dynamic_label(Label('Очки: {0}'.format(score),
                                     ((OFFSETS[player_num] +
                                       self.field_params.field_size / 2 +
                                       self.field_params.offset) * cell_size,
                                      screen_height - 2 * cell_size), WHITE))

    # рисует кружочки
    def put_dots(self, dots, offset):
        for (x, y) in dots:
            if x < 1 or y < 1 or x > self.field_params.field_size or \
                    y > self.field_params.field_size:
                continue
            x_d = x - 0.5 + offset + self.field_params.offset
            y_d = y + self.field_params.offset
            pygame.draw.circle(screen, DARK_BLUE,
                               (cell_size * x_d,
                                cell_size * (y_d - 0.5) + top_margin),
                               cell_size // 6)

    # рисует крестики
    @staticmethod
    def put_cross(x_start, y_start, color=DARK_BLUE):
        pygame.draw.line(screen, color, (x_start, y_start),
                         (x_start + cell_size, y_start + cell_size),
                         cell_size // 10)
        pygame.draw.line(screen, color, (x_start, y_start + cell_size),
                         (x_start + cell_size, y_start), cell_size // 10)

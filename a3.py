"""
CSSE1001 Project 3
Student name: Benjamin Patch

Used to assess the students ability to understand and utilies concepts of OOP
and GUI programming. Code given to use at the start of the project allows for
a simple and limited game to be played with very few features.

List of features added by student:
    - Ability to preview and place new towers with help from helper code
    - A status bar which allows the player to see information about the current game
    - File menu & dialog
    - Play controls (next wave and pause buttons)
    - Ability to sell towers
    - A variety of enemies and towers with different abilities (marked on level of skill required to create)
    - A shop to buy new towers
    - High scores

Classes involving the GUI of the Towers game.
TowerGameApp: Stepper class used as the top level GUI class.
StatusBar: A tk.Frame used for displaying current game status (wave, coins, etc.)
ShopTowerView: A tk.Frame used for displaying the shop.
"""
# standard libraries
from pathlib import Path
import math
import tkinter as tk
from tkinter import messagebox, simpledialog

# other modules
from model import TowerGame
from tower import SimpleTower, MissileTower, PulseTower
from advanced_towers import IceTower, EnergyTower
from enemy import SimpleEnemy
from advanced_enemy import FireEnemy, WoodEnemy, GroundEnemy
from utilities import Stepper, Countdown
from view import GameView
from level import AbstractLevel
from tower_view import TowerView
from high_score_manager import HighScoreManager

BACKGROUND_COLOUR = "#4a2f48"

__author__ = "Benjamin Patch"
__copyright__ = "Copyright 2018, Benjamin Patch"
__License__ = "MIT"


class MyLevel(AbstractLevel):
    """A simple game level containing examples of how to generate a wave"""
    waves = 30

    def get_wave(self, wave):
        """Returns enemies in the 'wave_n'th wave

        Parameters:
            wave_n (int): The nth wave

        Return:
            list[tuple[int, AbstractEnemy]]: A list of (step, enemy) pairs in the
                                             wave, sorted by step in ascending order 
        """
        enemies = []

        if wave == 1:
            # A hardcoded singleton list of (step, enemy) pairs

            enemies = [(10, SimpleEnemy())]
        elif wave == 2:
            # A hardcoded list of multiple (step, enemy) pairs

            enemies = [(10, SimpleEnemy()), (15, SimpleEnemy()), (30, SimpleEnemy())]
        elif 3 <= wave < 10:
            # List of (step, enemy) pairs spread across an interval of time (steps)

            steps = int(40 * (wave ** .5))  # The number of steps to spread the enemies across
            count = wave * 2  # The number of enemies to spread across the (time) steps

            for step in self.generate_intervals(steps, count):
                enemies.append((step, SimpleEnemy()))

        elif wave == 10:
            # Generate sub waves
            sub_waves = [
                # (steps, number of enemies, enemy constructor, args, kwargs)
                (1, 1, GroundEnemy, (), {}),
                (100, 20, FireEnemy, (), {}),
                (70, None, None, None, None),
                (50, 10, SimpleEnemy, (), {}),  # 10 enemies over 50 steps
                (100, None, None, None, None),  # then nothing for 100 steps
                (50, 15, SimpleEnemy, (), {})# then another 15 enemies over 50 steps
            ]

            enemies = self.generate_sub_waves(sub_waves)

        elif wave == 11:
            sub_waves = [
                 (1, 1, WoodEnemy, (), {}),
                 (250, None, None, None, None),
                 (50, 15, SimpleEnemy, (), {}),
                 (40, None, None, None, None),
                 (70, 20, FireEnemy, (), {})
            ]
            
            enemies = self.generate_sub_waves(sub_waves)
        else:  # 11 <= wave <= 20
            # Now it's going to get hectic
            if wave % 3 == 0:
                sub_waves = [
                    (
                        int(13 * wave),
                        int(5 * wave ** (wave/50)),
                        WoodEnemy,
                        (),
                        {},
                    ),
                    (
                        int(13 * wave),  # total steps
                        int(25 * wave ** (wave / 50)),  # number of enemies
                        SimpleEnemy,  # enemy constructor
                        (),  # positional arguments to provide to enemy constructor
                        {},  # keyword arguments to provide to enemy constructor
                    ),
                    (
                        int(15*wave),
                        int(25 * wave ** (wave/75)),
                        FireEnemy,
                        (),
                        {},
                    )
    
                ]
            elif wave % 3 == 1:
                sub_waves = [
                    
                    (
                        int(13 * wave),  # total steps
                        int(25 * wave ** (wave / 50)),  # number of enemies
                        SimpleEnemy,  # enemy constructor
                        (),  # positional arguments to provide to enemy constructor
                        {},  # keyword arguments to provide to enemy constructor
                    ),
                    (
                        int(13 * wave),
                        int(5 * wave ** (wave/75)),
                        WoodEnemy,
                        (),
                        {},
                    ),
                    (
                        int(15*wave),
                        int(25 * wave ** (wave/75)),
                        FireEnemy,
                        (),
                        {},
                    )
    
                ]
            elif wave % 3 == 2:
                sub_waves = [
                    (
                        int(13 * wave),
                        int(5 * wave ** (wave/75)),
                        WoodEnemy,
                        (),
                        {},
                    ),
                    (
                        int(15*wave),
                        int(25 * wave ** (wave/75)),
                        FireEnemy,
                        (),
                        {},
                    ),
                    (
                        int(13 * wave),  # total steps
                        int(25 * wave ** (wave / 50)),  # number of enemies
                        SimpleEnemy,  # enemy constructor
                        (),  # positional arguments to provide to enemy constructor
                        {},  # keyword arguments to provide to enemy constructor
                    )
                ]
            enemies = self.generate_sub_waves(sub_waves)

        return enemies


class TowerGameApp(Stepper):
    """Top-level GUI application for a simple tower defence game"""
    
    # pylint: disable=too-many-instance-attributes
    # I couldn't figure out how to fix certain bugs without defining a bunch of
    # variables at the start.
    
    # All private attributes for ease of reading
    _current_tower = None
    _paused = False
    _won = None

    _level = None
    _wave = None
    _score = None
    _coins = None
    _lives = None

    _master = None
    _game = None
    _view = None

    def __init__(self, master: tk.Tk, delay: int = 30):
        """Construct a tower defence game in a root window

        Parameters:
            master (tk.Tk): Window to place the game into
        """

        self._master = master
        master.title('Towers')
        super().__init__(master, delay=delay)

        self._game = game = TowerGame()

        self.setup_menu()

        # create a game view and draw grid borders
        self._view = view = GameView(master, size=game.grid.cells,
                                     cell_size=game.grid.cell_size,
                                     bg='antique white')
        view.pack(side=tk.LEFT, fill=tk.BOTH, expand=False)

#        # Task 1.3 (Status Bar): instantiate status bar
        
        self._level = MyLevel()
        self._status_bar = StatusBar(master, self._level.get_max_wave())
        self._status_bar.pack(fill=tk.BOTH, side=tk.TOP, expand=False)
        
        self._play_and_upgrades = tk.Frame(master, bg='white', height=40, width=200)
        self._play_and_upgrades.pack(side=tk.BOTTOM, expand=True, fill=tk.BOTH)
        self._pause_button = tk.Button(self._play_and_upgrades, text='Pause',
                                 command=self._toggle_paused)
        self._pause_button.pack(side=tk.LEFT, anchor=tk.N, expand=False)
        self._pause_button.place(x=160, y=0)
        self._next_wave_button = tk.Button(self._play_and_upgrades, text='Next Wave',
                                     command=self.next_wave)
        self._next_wave_button.pack(side=tk.LEFT, anchor=tk.N, expand=False)
        self._next_wave_button.place(x=90, y=0)
        
        #highscores object
        self._high_scores = HighScoreManager()
        
        #Used for fixing bug where clicking New Game would make game faster
        try:
            if self._new_game_called:
                pass
        except AttributeError: #raised when new_game hasn't been called
            self._new_game_count = 0
        #whether upgrades has been called before. Whether to clear upgrade buttons
        #or not.
        self._called_before = 0
        self._speed_upgrade = 0
        self._simple_upgrade = 0
        self._no_coins_ice = 0
        self._no_coins_speed = 0
        self._missile_upgrade = 0
        self._no_coins_simple = 0
        self._ice_upgrade = 0
        self._confirm_upgrades = 0
        
        #Shop Class instantiation
        self._towers = towers = [
            MissileTower,
            IceTower,
            PulseTower,
            EnergyTower
        ]
    
        self._shop = tk.Frame(master, bg='purple')
        self._shop.pack(fill=tk.BOTH, side=tk.BOTTOM, expand=False)
#    
##         Create views for each tower & store to update if availability changes
#        self._tower_views = []
#        col = 0
#        for tower_class in towers:
#            tower = tower_class(self._game.grid.cell_size)
#            self._shop_view = ShopTowerView(self._shop, tower_class, #highlight="#4b3b4a",
#                                 click_command=lambda class_=tower_class: self.select_tower(class_), bg=colours[col])
#            self._shop_view.pack(fill=tk.BOTH, side=tk.TOP, expand=True)
#            self._tower_views.append((tower, self._shop_view))  
#            Can use to check if tower is affordable when refreshing view
#            col+=1
        
        self._tower_views = []
        col = 0
        for tower_class in towers:
#            tower = tower_class(self._game.grid.cell_size // 2)
            tower = tower_class(30)
            view = ShopTowerView(self._shop, tower, bg='purple',#, highlight="#4b3b4a",
                         click_command=lambda class_=tower_class: self.select_tower(class_))
            view.pack(fill=tk.X)
            self._tower_views.append((tower, view))
            col += 1
        
#         Task 1.5 (Play Controls): instantiate widgets here

        # bind game events
        game.on("enemy_death", self._handle_death)
        game.on("enemy_escape", self._handle_escape)
        game.on("cleared", self._handle_wave_clear)

        # Task 1.2 (Tower Placement): bind mouse events to canvas here
        self._view.bind("<Button-1>", self._left_click)
        self._view.bind("<Motion>", self._move)
        self._view.bind("<Leave>", self._mouse_leave)
        self._view.bind("<Button-3>", self._right_click)
        # Level
        self._level = MyLevel()

        self.select_tower(MissileTower)

        self._view.draw_borders(game.grid.get_border_coordinates())

        # Get ready for the game
        self._setup_game()

        # Remove the relevant lines while attempting the corresponding section
        # Hint: Comment them out to keep for reference

        # Task 1.2 (Tower Placement): remove these lines
#        towers = [
#            ([(2, 2), (3, 0), (4, 1), (4, 2), (4, 3)], SimpleTower),
#            ([(2, 5)], PulseTower)
#        ]
#
#        for positions, tower in towers:
#            for position in positions:
#                self._game.place(position, tower_type=tower)
#
##         Task 1.5 (Tower Placement): remove these lines
#        self._game.queue_wave([], clear=True)
#        self._wave = 4 - 1  # first (next) wave will be wave 4
#        self.next_wave()
##
##        # Task 1.5 (Play Controls): remove this line
#        self.start()

    def setup_menu(self):
        """Sets up the menu bar with New Game, Exit and High Scores commands"""
        self._menubar = tk.Menu(self._master)
        self._filemenu = tk.Menu(self._menubar, tearoff=0)
        self._filemenu.add_command(label='New Game', command=self._new_game)
        self._filemenu.add_command(label='Exit', command=self._exit)
        self._filemenu.add_command(label="High Scores", command=self._display_high_scores)
        self._menubar.add_cascade(label='File', menu=self._filemenu)
        self._master.config(menu=self._menubar)

    def _toggle_paused(self, paused=None):
        """Toggles or sets the paused state

        Parameters:
            paused (bool): Toggles/pauses/unpauses if None/True/False, respectively
        """
        if paused is None:
            paused = not self._paused
        if paused:
            self.pause()
        else:
            self.start()
        if paused:
            self._pause_button.configure(text='Play')
        else:
            self._pause_button.configure(text='Pause')

        self._paused = paused

    def _setup_game(self):
        """
        Sets up status_bar variables, pause/next wave buttons.
        Starts a game from wave 1.
        """
        self._wave = 0
        self._score = 0
        self._coins = 80
        self._lives = 20
        self._won = False
        
        #status_bar display setup
        self._status_bar.set_wave_display(self._wave, self._level.get_max_wave())
        self._status_bar.set_coin_display(self._coins)
        self._status_bar.set_lives_display(self._lives)
        self._status_bar.set_score_display(self._score)
        
        #activate the pause and next wave buttons
        self._next_wave_button.configure(state='active')
        self._pause_button.configure(state='active', text='Pause')

        self._game.reset()

        # Auto-start the first wave
        self.next_wave()
        self._toggle_paused(paused=False)

    # Task 1.4 (File Menu): Complete menu item handlers here (including docstrings!)
    #
    def _new_game(self):
        """
        Called by clicking "New Game" in menubar.
        Starts a new game.
        """
#        self._view.forget()
#        self._status_bar.forget()
#        self._shop.forget() 
#        self._play_and_upgrades.forget()
#        self._new_game_count += 1
#        self._new_game_called = 1
#        self.__init__(self._master, delay=(30 + self._new_game_count*30))
        self._setup_game()
    #
    def _exit(self):
        """Yes/No question confirming whether to close or not."""
        if messagebox.askyesno("Confirm Exit", "Are you sure you want to exit?"):
            self._master.destroy()

    def refresh_view(self):
        """Refreshes the game view"""
        if self._step_number % 2 == 0:
            self._view.draw_enemies(self._game.enemies)
        self._view.draw_towers(self._game.towers)
        self._view.draw_obstacles(self._game.obstacles)

    def _step(self):
        """
        Perform a step every interval

        Triggers a game step and updates the view

        Returns:
            (bool) True if the game is still running
        """
        self._game.step()
        self.refresh_view()

        return not self._won
    
    def _move(self, event):
        """
        Handles the mouse moving over the game view canvas

        Parameter:
            event (tk.Event): Tkinter mouse event
        """
        if self._current_tower.get_value() > self._coins:
            self._view.delete('shadow', 'range', 'path')
            return

        # move the shadow tower to mouse position
        position = event.x, event.y
        self._current_tower.position = position

        legal, grid_path = self._game.attempt_placement(position)

        # find the best path and covert positions to pixel positions
        path = [self._game.grid.cell_to_pixel_centre(position)
                for position in grid_path.get_shortest()]
        self._view.draw_preview(self._current_tower, legal)
        self._view.draw_path(path)

    def _mouse_leave(self, event):
        """Deletes the preview when cursor leaves game canvas."""
        self._view.delete('shadow', 'range', 'path')

    def _left_click(self, event):
        """
        Attempts to place self._current_tower on the clicked square.
        
        Parameter:
            event (tk.Event): Tkinter mouse event
        """
        # retrieve position to place tower
        position = event.x, event.y
        cell_position = self._game.grid.pixel_to_cell(position)
        if self.is_paused():
            return
        
        if cell_position in self._game.towers.keys():
            self._get_upgrades(cell_position)
            return
        
        if self._current_tower is None:
            return
        
        if self._current_tower.get_value() > self._coins:
            return

        if self._game.place(cell_position, tower_type=self._current_tower.__class__):
            # Task 1.2 (Tower placement): Attempt to place the tower being previewed
            self._coins -= int(self._current_tower.base_cost)
            self._status_bar.set_coin_display(self._coins)
            for tower_view in self._tower_views:
                if tower_view[0].base_cost > self._coins:
                    # pylint: disable=protected-access
                    # This only has effects intended
                    tower_view[1].update_price_colour('red')
                    
    def _get_upgrades(self, cell_position):
        """
        Adds checkboxes to upgrade area according to the tower clicked, if 
        self._coins allows. Otherwise, shows message stating insufficient funds
        
        Parameters:
            cell_position (tuple): which cell was clicked
        """
        for label in [self._speed_upgrade,
                self._no_coins_ice,
                self._no_coins_speed,
                self._no_coins_simple,
                self._missile_upgrade,
                self._ice_upgrade,
                self._confirm_upgrades]:
            try:
                label.destroy()
            except AttributeError: #attribute error raised if that upgrade option
                continue           #hasn't been made previously
        
        self._called_before = 1
        
        
        #checks type of tower clicked, current coins and displays options accordnly
        self._tower_to_upgrade = tower_clicked = self._game.towers[cell_position]
        self._speed_clicked = tk.IntVar()
        self._ice_upgrade_clicked = tk.IntVar()
        self._range_upgrade_clicked = tk.IntVar()
        self._simple_upgrade_clicked = tk.IntVar()
        self._confirm_upgrades = tk.Button(self._play_and_upgrades, text='Confirm',
                                     command=self._upgrade_tower)
        self._confirm_upgrades.pack(side=tk.RIGHT)
        self._confirm_upgrades.place(x=238, y=55)
        
        if self._coins >= 100:
            self._speed_upgrade = tk.Checkbutton(self._play_and_upgrades,
                                           text='Speed Upgrade               100 coins',
                                           variable=self._speed_clicked, bg='white',
                                           offvalue=0, onvalue=1)
            self._speed_upgrade.pack(side=tk.LEFT, expand=False)
        else:
            self._no_coins_speed = tk.Label(self._play_and_upgrades, 
                                      text='Not enough coins for speed upgrade')
            self._no_coins_speed.pack(side=tk.LEFT, expand=False)
        if tower_clicked.name == 'Ice Tower' and self._coins >= 250:
            self._ice_upgrade = tk.Checkbutton(self._play_and_upgrades,
                                        text='Ice Tower Upgrade        250 coins',
                                        variable=self._ice_upgrade_clicked,
                                        bg='white')
            self._ice_upgrade.pack(side=tk.LEFT, expand=False)
            self._ice_upgrade.place(x=0, y=70)
        elif tower_clicked.name == 'Ice Tower' and self._coins < 250:
            self._no_coins_ice = tk.Label(self._play_and_upgrades,
                                    text='Not enough coins for Ice Tower upgrade')
            self._no_coins_ice.pack(side=tk.LEFT, expand=False)
            self._no_coins_ice.place(x=0, y=70)
        if tower_clicked.name == 'Simple Tower' and self._coins >= 40:
            self._simple_upgrade = tk.Checkbutton(self._play_and_upgrades,
                                    text='Level Upgrade                40 coins',
                                        variable=self._simple_upgrade_clicked,
                                        bg='white')
            self._simple_upgrade.pack(side=tk.LEFT, expand=False)
            self._simple_upgrade.place(x=0, y=70)
        elif tower_clicked.name == 'Simple Tower' and self._coins < 40:
            self._no_coins_simple = tk.Label(self._play_and_upgrades,
                                     text='Not enough coins for Simple Tower upgrade')
            self._no_coins_simple.pack(side=tk.LEFT, expand=False)
            self._no_coins_simple.place(x=0, y=70)
    def _upgrade_tower(self):
        """
        Checks which checkboxes were ticked at time of confirming.
        Upgrades accordinly.
        """
        if self._speed_clicked.get() == 1:
            if self._tower_to_upgrade.cool_down_steps > 0:
                self._tower_to_upgrade.cool_down_steps -= 1
                self._tower_to_upgrade.cool_down = Countdown(self._tower_to_upgrade.cool_down_steps)#speeds up by 10%
                self._speed_clicked = 0
                self._coins -= 100
        if self._range_upgrade_clicked.get() == 1:
            if self._tower_to_upgrade.range.outer_radius != 5:
                self._tower_to_upgrade.range.outer_radius = 5
                self._coins -= 25
                self._range_upgrade_clicked = 0
        if self._ice_upgrade_clicked.get() == 1:
            self._tower_to_upgrade.upgraded = True
            self._tower_to_upgrade.level += 1
            self._tower_to_upgrade.colour = 'blue4'
            self._coins -= 250
        if self._simple_upgrade_clicked.get() == 1:
            self._tower_to_upgrade.level += 1
            self._coins -= 40
            self._simple_upgrade.destroy()
            
        for label in [self._speed_upgrade,
                      self._no_coins_ice,
                      self._no_coins_speed,
                      self._no_coins_simple,
                      self._simple_upgrade,
                      self._missile_upgrade,
                      self._ice_upgrade,
                      self._confirm_upgrades]:
            try:
                label.destroy()
                self._simple_upgrade.destroy()
            except AttributeError:
                pass
    def _right_click(self, event):
        """
        Attempts to sell tower in clicked grid
        Parameters:
            event (tk.Event): Tkinter mouse event
        """
        position = event.x, event.y
        position = self._game.grid.pixel_to_cell(position)
        if position in self._game.towers.keys():
            # Add 80% of tower's base_cost to player's wallet
            self._coins += int(0.8*self._game.towers[position].base_cost)
            self._status_bar.set_coin_display(self._coins)
            del self._game.towers[position]
            for tower_view in self._tower_views:
                if tower_view[0].base_cost < self._coins:
                    # pylint: disable=protected-access
                    # This only has effects intended
                    tower_view[1].update_price_colour('white')

    def next_wave(self):
        """Sends the next wave of enemies against the player"""
        #checks whether it should do anything
        if self._wave == self._level.get_max_wave():
            self._next_wave_button.configure(state='disabled')
            return
        
        self._wave += 1
        self._pause_button.configure(text='Pause')
        
        #checks to disable button but still continues with wave.
        if self._wave == self._level.get_max_wave():
            self._next_wave_button.configure(state='disabled')

#        # Task 1.3 (Status Bar): Update the current wave display here
        self._status_bar.set_wave_display(self._wave, self._level.get_max_wave())

        # Generate wave and enqueue
        wave = self._level.get_wave(self._wave)
        for step, enemy in wave:
            enemy.set_cell_size(self._game.grid.cell_size)

        self._game.queue_wave(wave)
        self.start()

    def select_tower(self, tower):
        """
        Set 'tower' as the current tower

        Parameters:
            tower (AbstractTower): The new tower type
        """
        self._current_tower = tower(self._game.grid.cell_size)

    def _handle_death(self, enemies):
        """
        Handles enemies dying

        Parameters:
            enemies (list<AbstractEnemy>): The enemies which died in a step
        """
        bonus = len(enemies) ** .5
        for enemy in enemies:
            self._coins += enemy.points
            self._score += int(enemy.points * bonus)

        # Task 1.3 (Status Bar): Update coins & score displays here
        self._status_bar.set_coin_display(self._coins)
        self._status_bar.set_score_display(self._score)
        for tower_view in self._tower_views:
            if tower_view[0].base_cost <= self._coins:
                # pylint: disable=protected-access
                # This only has effects intended
                tower_view[1].update_price_colour('white')

    def _handle_escape(self, enemies):
        """
        Handles enemies escaping (not being killed before moving through the grid

        Parameters:
            enemies (list<AbstractEnemy>): The enemies which escaped in a step
        """
        self._lives -= len(enemies)
        if self._lives < 0:
            self._lives = 0

        # Task 1.3 (Status Bar): Update lives display here
        self._status_bar.set_lives_display(self._lives)

        # Handle game over
        if self._lives == 0:
            self._handle_game_over(won=False)

    def _handle_wave_clear(self):
        """Handles an entire wave being cleared (all enemies killed)"""
        if self._wave == self._level.get_max_wave():
            self._handle_game_over(won=True)

        # Task 1.5 (Play Controls): remove this line
        #self.next_wave()

    def _handle_game_over(self, won=False):
        """Handles game over
        
        Parameter:
            won (bool): If True, signals the game was won (otherwise lost)
        """
        
        if self._high_scores.does_score_qualify(self._score):
            high_score_name = simpledialog.askstring("Input",
                                                     "Your score qualified for "\
                                                     "the high scores, what is"\
                                                     " your name?")
            self._high_scores.add_entry(high_score_name, self._score)
        
        if won:
            win_or_lose = 'finished'
        else:
            win_or_lose = 'didn\'t finish'
        messagebox.showinfo('Game Over', 'You %s with a score of %s' % (win_or_lose, self._score))
        self._high_scores.save()
        
        self.stop()
        
    def _display_high_scores(self):
        """Displays the current high scores"""
        display = ''
        entries = self._high_scores.get_entries()
        for i in range(len(self._high_scores.get_entries())):
            try:
                display += str(entries[i]['name'] + ' - Score: ' +\
                               str(entries[i]['score']) + entries[i]['data'] + '\n')
            except TypeError:
                if entries[i]['name']: #accounts for people entering nothing for their name
                    display += str(str(entries[i]['name']) + ' - Score: ' +\
                                   str(entries[i]['score']) + '\n')
                else:
                    display += str('*NO NAME ENTERED*' + ' - Score: ' +\
                                   str(entries[i]['score']) + '\n')
        messagebox.showinfo("High Scores", str(display))

class StatusBar(tk.Frame):
    """Tkinter frame used for displaying information about current game"""
    def __init__(self, master, max_wave):
        """
        Constructs display of coins, lives, score and wave
        
        Parameters:
            master (tk.Tk): Master frame in which status_bar is.
            max_wave (int): The number of the final wave in the game.
        """
        super().__init__(master, bg='white', width=200, height=50)
        self._coin_path = Path("images/coins.gif")
        self._heart_path = Path("images/heart.gif")
        self._coin = tk.PhotoImage(master=self, file=self._coin_path)
        self._heart = tk.PhotoImage(master=self, file=self._heart_path)
        self._wave = str('Wave: ' + str(1) + '/' + str(max_wave)) 
        self._coins = str(str(80) + ' coins   ')
        self._score = str(0)
        self._lives = str(str(20) + ' lives')
        
        self._wave_label = tk.Label(self, text=self._wave, bg='white',
                                    font=('Courier', 13))
        self._wave_label.pack(side=tk.TOP, expand=False)
        
        self._score_label = tk.Label(self, text=self._score, bg='white',
                                     font=('Courier', 13))
        self._score_label.pack(side=tk.TOP, expand=False)
        
        self._coins_image = tk.Label(self, image=self._coin, bg='white')
        self._coins_image.pack(side=tk.LEFT, anchor=tk.NW, expand=False)
        self._coins_text = tk.Label(self, text=self._coins, bg='white',
                                    font=("Courier", 13))
        self._coins_text.pack(side=tk.LEFT, anchor=tk.NW, pady=6, expand=False)
        self._lives_image = tk.Label(self, image=self._heart, bg='white')
        self._lives_image.pack(side=tk.LEFT, anchor=tk.NW, expand=False)
        self._lives_text_label = tk.Label(self, text=self._lives, bg='white',
                                          font=("Courier", 13))
        self._lives_text_label.pack(side=tk.LEFT, anchor=tk.NW, pady=6, expand=False)
        
    def set_wave_display(self, new_wave, max_wave):
        """
        Sets the wave display
        
        Parameters:
            new_wave (int): The wave that the game has changed to.
            max_wave (int): The number of the final wave in the game.
        """
        self._wave = str('Wave: ' + str(new_wave) + '/' + str(max_wave)) 
        self._wave_label.configure(text=self._wave)

    def set_score_display(self, score):
        """
        Sets the score display
        
        Parameters:
            score (int): Current score
        """
        self._score = str(score)
        self._score_label.configure(text=self._score)
        
    def set_coin_display(self, coins):
        """
        Sets the coin display
        
        Parameters:
            coins (int): Current number of coins
        """
        self._coins = str(str(coins) + ' coins   ')
        self._coins_text.configure(text=self._coins)
        
    def set_lives_display(self, lives):
        """
        Sets the lives display
        
        Parameters:
            lives (int): Current number of lives
        """
        self._lives = str(str(lives) + ' lives')
        self._lives_text_label.configure(text=self._lives)

        
class ShopTowerView(tk.Frame):
    """One tower in the shop for buying new towers"""
    def __init__(self, master, tower, bg, click_command):
        """
        Creates a view of the tower in the shop displaying name and price.
        Creates a canvas which, when clicked on, changes the current tower and
        allows you to preview/place this tower.
        
        Parameters:
            master (tk.Frame): Frame which view is located.
            tower (tower_class): The type of tower.
            bg (str): The colour for the background.
            click_command (lambda command): Command for changing current_tower
        """
        super().__init__(master, bg=bg)
        self._canvas = tk.Canvas(self, bg='purple', height=35, width=30)
        self._canvas.pack(side=tk.LEFT, expand=False)
        self._canvas.bind('<Button-1>', self._left_click)
        self._click_command = click_command
        self._tower_name = tk.Label(self, text=str(tower.name), bg='purple',
                                    fg='white')
        self._tower_name.pack(side=tk.TOP, expand=True)
        self._tower_price = tk.Label(self, text=str(tower.base_cost),
                                     bg='purple', fg='red')
        self._tower_price.pack(side=tk.TOP, expand=True)
        #tower.position = (tower.cell_size // 2, tower.cell_size // 2)  # Position in centre
        tower.position = (16, 18)
        tower.rotation = 3 * math.pi / 2  # Point up
        TowerView.draw(self._canvas, tower, tower.cell_size)
        if tower.name == 'Simple Tower':
            self.update_price_colour('white')
        
        
    def _left_click(self, event):
        """
        Performs the click command, which changes the current tower.
        
        Parameters:
            event (tk.Event): Tkinter mouse event.
        """
        self._click_command()
    
    def update_price_colour(self, colour):
        """
        Changes the colour for the text displaying price of tower.
        Used when enough coins are gained for this tower, or when not enough coins
        are owned.
        
        Parameters:
            colour (str): The colour to be changed to.
        """
        self._tower_price.configure(fg=colour)
        
def main():
    """Initiates the main Tkinter window"""
    root = tk.Tk()
    root.geometry('650x360')
    root.config(bg='white')
    app = TowerGameApp(root)
    root.mainloop()
    
if __name__ == "__main__":
    main()

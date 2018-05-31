"""
Provides the implementation of a variety of enemies to be used in the game.
"""

from enemy import AbstractEnemy, SimpleEnemy
from utilities import rectangles_intersect, get_delta_through_centre
class WoodEnemy(SimpleEnemy):
    """An enemy that moves slowly but is immune to slows and has a lot of health"""
    colour = 'peru'
    points = 40
    
    def __init__(self, grid_size=(.2, .2), grid_speed=2/60, health=1500):
        super().__init__(grid_size, grid_speed, health)

    def damage(self, damage, type_):
        self.health -= damage
        if self.health < 0:
            self.health = 0
class FireEnemy(SimpleEnemy):
    """An enemy that moves very quickly, killed by ice towers"""
    name = "Fire Enemy"
    colour = 'orange red'
    points = 2
    def __init__(self, grid_size=(.2, .2), grid_speed=10/60, health=350):
        super().__init__(grid_size, grid_speed, health)
        self.slowed = False

    def damage(self, damage, type_):
        """Enemy never takes damage

        Parameters:
            damage (int): The amount of damage to inflict
            type_ (str): The type of damage to do i.e. projectile, explosive
        """
        self.health -= damage
        if self.health < 0:
            self.health = 0

class GroundEnemy(AbstractEnemy):
    """Basic type of enemy"""
    name = "Ground Enemy"
    colour = 'black'

    points = 5

    def __init__(self, grid_size=(.2, .2), grid_speed=5/60, health=100):
        super().__init__(grid_size, grid_speed, health)

    def damage(self, damage, type_):
        """Inflict damage on the enemy

        Parameters:
            damage (int): The amount of damage to inflict
            type_ (str): The type of damage to do i.e. projectile, explosive
        """
        if type_ == 'energy':
            self.health -= damage
            if self.health < 0:
                self.health = 0

    def step(self, data):
        """Move the enemy forward a single time-step

        Parameters:
            grid (GridCoordinateTranslator): Grid the enemy is currently on
            path (Path): The path the enemy is following

        Returns:
            bool: True iff the new location of the enemy is within the grid
        """
        grid = data.grid
        path = data.path

        # Repeatedly move toward next cell centre as much as possible
        movement = self.grid_speed
        while movement > 0:
            cell_offset = grid.pixel_to_cell_offset(self.position)

            # Assuming cell_offset is along an axis!
            offset_length = abs(cell_offset[0] + cell_offset[1])

            if offset_length == 0:
                partial_movement = movement
            else:
                partial_movement = min(offset_length, movement)

            cell_position = grid.pixel_to_cell(self.position)
            delta = path.get_best_delta(cell_position)

            # Ensures enemy will move to the centre before moving toward delta
            dx, dy = get_delta_through_centre(cell_offset, delta)

            speed = partial_movement * self.cell_size
            self.move_by((speed * dx, speed * dy))
            self.position = tuple(int(i) for i in self.position)

            movement -= partial_movement

        intersects = rectangles_intersect(*self.get_bounding_box(), (0, 0), grid.pixels)
        return intersects or grid.pixel_to_cell(self.position) in path.deltas
    
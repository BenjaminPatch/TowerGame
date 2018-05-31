"""
Tower classes for advanced tower(s) in task 3
"""

import math
from typing import Union

from enemy import AbstractEnemy
from range_ import CircularRange, DonutRange
from utilities import euclidean_distance, rotate_toward, angle_between,\
polar_to_rectangular
from tower import AbstractTower, AbstractObstacle, SimpleTower
    
class IceTower(AbstractTower):
    """A tower that slows SimpleEnemy, kills FireEnemy, 
    doesn't do anything to WoodEnemy.
    When upgraded, IceTower does damage to SimpleEnemy as well."""
    name = 'Ice Tower'
    colour = 'cyan'

    cool_down_steps = 5

    base_cost = 60
    level_cost = 45
    base_damage = 150
    def __init__(self, cell_size: int, grid_size=(.9, .9), rotation=math.pi * .25, base_damage=150, level: int = 1):
        super().__init__(cell_size, grid_size, rotation, base_damage, level)
        self.upgraded = False
    range = CircularRange(1.3)
    def get_fire_targets(self, units):
        '''Gets all enemies in range'''
        target = []
        count = 1
        try:
            next_target = self.get_units_in_range(units.enemies)
            target.append(next_target.__next__())
            while count < 15:
                i = len(target)
                new_target = next_target.__next__()
                if new_target not in target:
                    target.append(new_target)
                    if i == len(target):
                        break
                count += 1
        except StopIteration:
            return target

        return target

    def step(self, units):
        """Deals damage to nearby FireEnemies, slows SimpleEnemies"""
        self.cool_down.step()

        if not self.cool_down.is_done():
            return

        target = self.get_fire_targets(units)
        if target == []:
            return
        for enemy in target:
            if(enemy.name == 'Fire Enemy' and not enemy.slowed):
                enemy.slowed = True
                enemy.damage(self.get_damage(), 'projectile')
            elif(enemy.name == 'Fire Enemy' and enemy.slowed):
                enemy.damage(self.get_damage(), 'projectile')
            elif (enemy.name == 'Simple Enemy' and self.upgraded):
                enemy.damage(15, 'projectile')
            elif (enemy.grid_speed == 5/60 and enemy.name == 'Simple Enemy'):
                enemy.grid_speed *= 0.80
            
            self.cool_down.start()
        
class EnergyPulse(AbstractObstacle):
    """A simple projectile fired from a MissileTower"""
    name = "Energy Pulse"
    colour = 'green'  # Eburnean

    rotation_threshold = (1 / 3) * math.pi

    def __init__(self, position, cell_size, target: AbstractEnemy, size=.2,
                 rotation: Union[int, float] = 0, grid_speed=.1, damage=10):
        super().__init__(position, (size, 0), cell_size, grid_speed=grid_speed, rotation=rotation, damage=damage)
        self.target = target

    def step(self, units):
        """Performs a time step for this missile
        
        Moves towards target and damages if collision occurs
        If target is dead, this missile expires
        
        Parameters:
            units.enemies (UnitManager): The unit manager to select targets from
            
        Return:
            (persist, new_obstacles) pair, where:
                - persist (bool): True if the obstacle should persist in the game (else will be removed)
                - new_obstacles (list[AbstractObstacle]): A list of new obstacles to add to the game, or None
        """
        if self.target.is_dead():
            return False, None

        # move toward the target
        radius = euclidean_distance(self.position, self.target.position)

        if radius <= self.speed:
            self.target.damage(self.damage, 'energy')
            return False, None

        # Rotate toward target and move
        angle = angle_between(self.position, self.target.position)
        self.rotation = rotate_toward(self.rotation, angle, self.rotation_threshold)

        dx, dy = polar_to_rectangular(self.speed, self.rotation)
        x, y = self.position
        self.position = x + dx, y + dy

        return True, None

class EnergyTower(SimpleTower):
    """A tower that fires energy that track a target"""
    name = 'Energy Tower'
    colour = 'green'

    cool_down_steps = 10

    base_cost = 80
    level_cost = 60

    range = DonutRange(1.5, 4.5)

    rotation_threshold = (1 / 3) * math.pi

    def __init__(self, cell_size: int, grid_size=(.9, .9), rotation=math.pi * .25, base_damage=150, level: int = 1):
        super().__init__(cell_size, grid_size=grid_size, rotation=rotation, base_damage=base_damage, level=level)

        self._target: AbstractEnemy = None

    def _get_target(self, units) -> Union[AbstractEnemy, None]:
        """Returns previous target, else selects new one if previous is invalid
        
        Invalid target is one of:
            - dead
            - out-of-range
        
        Return:
            AbstractEnemy: Returns previous target, unless it is non-existent or invalid (see above),
                           Otherwise, selects & returns new target if a valid one can be found,
                           Otherwise, returns None
        """

        if self._target is None \
                or self._target.is_dead() \
                or not self.is_position_in_range(self._target.position):
            self._target = self.get_unit_in_range(units)

        return self._target

    def step(self, units):
        """Rotates toward 'target' and fires missile if possible"""
        self.cool_down.step()

        target = self._get_target(units.enemies)
        if target is None:
            return None

        # Rotate toward target
        angle = angle_between(self.position, target.position)
        partial_angle = rotate_toward(self.rotation, angle, self.rotation_threshold)

        self.rotation = partial_angle

        if angle != partial_angle or not self.cool_down.is_done():
            return None

        self.cool_down.start()

        # Spawn missile on tower
        pulse = EnergyPulse(self.position, self.cell_size, target, rotation=self.rotation,
                          damage=self.get_damage(), grid_speed=.3)

        # Move missile to outer edge of tower
        radius = self.grid_size[0] / 2
        delta = polar_to_rectangular(self.cell_size * radius, partial_angle)
        pulse.move_by(delta)

        return [pulse]
    
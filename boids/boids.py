"""A very basic implementation of the boids algorithm as made famous by
C Reynolds in "Flocks, Herds, and Schools: A Distributed Behavioral Model"

The primarily source was:
    http://www.vergenet.net/~conrad/boids/pseudocode.html by Conrad Parker.

Reynolds, C. W. (1987)
Flocks, Herds, and Schools: A Distributed Behavioral Model
in Computer Graphics, 21(4) (SIGGRAPH '87 Conference Proceedings) pages 25-34.
    https://www.red3d.com/cwr/papers/1987/boids.html

Rules:
- cohesion: steer to move towards the average position (center of mass) of
   local flockmates
- alignment: steer towards the average heading of local flockmates
- separation: steer to avoid crowding local flockmates

Additional rules:
- speed limit: boids shouldn't move too quickly, nor should they move too
  slowly either.

Future:
- Limit the area in which they can fly
-- Video game style wrapping as seen here
    https://lufemas.github.io/boid-ai-implementation/
-- "Bounding the position" in the "Boids Pseudocode" page above.
    Essentially treat the edge like something they want to avoid so it
    causes them to turn around.
"""

import math
import random

LOCAL_RANGE = 225.0  # Distance units.

TOO_CLOSE_RANGE = 5.0

def dot(a, b):
    """Perform dot product on two vectors."""
    return sum(i * j for i, j in zip(a, b))


def limit_magnitude(vector, min_magnitude, max_magnitude):
    mag = math.sqrt(sum(i ** 2 for i in vector))
    if mag > max_magnitude:
        normalizing_factor = max_magnitude / mag
    elif mag < min_magnitude:
        normalizing_factor = min_magnitude / mag
    else:
        return vector

    return [value * normalizing_factor for value in vector]


class Point:
    """
    Basic point class with just enough to make pseudocode easily appliable.
    """

    def __init__(self, x, y):
        self.x = x
        self.y = y

    def __len__(self):
        return 2

    def __iter__(self):
        return iter([self.x, self.y])

    def __getitem__(self, index):
        if index == 0:
            return self.x
        elif index == 1:
            return self.y
        else:
            raise IndexError()

    def __iadd__(self, rhs):
        self.x += rhs.x
        self.y += rhs.y
        return self


class Vector:
    """
    Basic vector class with just enough to make pseudocode easily appliable.
    """

    def __init__(self, x, y):
        self.x = x
        self.y = y

    def __len__(self):
        return 2

    def __getitem__(self, index):
        if index == 0:
            return self.x
        elif index == 1:
            return self.y
        else:
            raise IndexError()

    def __add__(self, rhs):
        if isinstance(rhs, tuple):
            return Vector(self.x + rhs[0], self.y + rhs[1])
        return Vector(self.x + rhs.x, self.y + rhs.y)

    def __iadd__(self, rhs):
       self.x += rhs.x
       self.y += rhs.y
       return self

    def __mul__(self, rhs):
        self.x *= rhs
        self.y *= rhs
        return self


class Boid:
    """A generic simulated flocking creature"""

    # This effects where the boid can see and thus where it can see its
    # flockmates.
    VIEW_ANGLE = 110  # Degrees

    # Speed limits to avoid the boids from moving too quickly and stopping.
    MIN_SPEED = 20.0
    MAX_SPEED = 180.0

    def __init__(self, initial_position, initial_velocity):
        self.position = Point(*initial_position)
        self.velocity = Vector(*initial_velocity)

    def find_local_flockmates(self, all_boids):
        """Find the flockmates that are near this boid.

        "The neighbourhood is characterized by a distance (measured from the
        center of the boid) and an angle, measured from the boid's direction
        of flight" - Craig Reynolds
        """

        x, y = self.position
        speed = math.sqrt((self.velocity[0] ** 2) + (self.velocity[1] ** 2))

        for boid in all_boids:
            if boid == self:
                continue

            difference = (boid.position[0] - x, boid.position[1] - y)

            # TOOD: Could adjust this to be simply the squared distance to
            # avoid sqrt.
            distance = math.sqrt((difference[0] ** 2) + (difference[1] ** 2))

            # Determine the view angle
            angle = math.degrees(
                math.acos(dot(self.velocity, difference) / (speed * distance)))

            if distance < LOCAL_RANGE and angle < self.VIEW_ANGLE:
                yield boid


def rule1(current_boid, flockmates):
    """
    Rule 1: Boids try to fly towards the centre of mass of neighbouring boids.

    This is cohesion.
    """

    def average_position(boids):
        if not boids:
            # This maybe should be centre of screen (or find nearest flock).
            return 0.0, 0.0

        sum_x = sum(boid.position[0] for boid in boids)
        sum_y = sum(boid.position[1] for boid in boids)
        return sum_x / len(boids), sum_y / len(boids)

    centre_of_mass = average_position(flockmates)

    cohesion_vector = tuple(
        (avg - p) * 0.03 for avg, p in zip(centre_of_mass, current_boid.position)
        )

    return Vector(*cohesion_vector)


def rule2(current_boid, all_boids):
    """
    Rule 2: Boids try to keep a small distance away from other objects
    (including other boids).
    """

    x, y = current_boid.position

    c_x = 0.0
    c_y = 0.0

    for boid in all_boids:
        if boid != current_boid:
            difference = (boid.position[0] - x, boid.position[1] - y)
            distance = math.sqrt((difference[0] ** 2) + (difference[1] ** 2))
            if distance < TOO_CLOSE_RANGE:
                inv_sqr_magnitude = 1 / (distance ** 2)
                c_x -= difference[0] * inv_sqr_magnitude
                c_y -= difference[1] * inv_sqr_magnitude

    return Vector(*limit_magnitude([c_x, c_y], 0.0, 1.0)) * 7.5


def rule3(current_boid, flockmates):
    """
    Rule 3: Boids try to match velocity with near boids

    This is indirectly alignment as velocity is direction.
    """

    if not flockmates:
        # No nearby boids. maybe should fallback to using all of them.
        return (0.0, 0.0)

    velocity_x = 0.0
    velocity_y = 0.0

    for mate in flockmates:
        # To date the flockmates are computed to exclude the current boid.
        assert mate != current_boid
        velocity_x += mate.velocity[0]
        velocity_y += mate.velocity[1]

    velocity_x = velocity_x / len(flockmates)
    velocity_y = velocity_y / len(flockmates)

    return Vector(
        (velocity_x - current_boid.velocity[0]) * 0.045,
        (velocity_y - current_boid.velocity[1]) * 0.045,
    )


def move_all_boids_to_new_positions(boids):
    # Based on the pseudocode from:
    # http://www.vergenet.net/~conrad/boids/pseudocode.html
    for boid in boids:
        flockmates = list(boid.find_local_flockmates(boids))

        v1 = rule1(boid, flockmates)
        v2 = rule2(boid, flockmates)
        v3 = rule3(boid, flockmates)

        boid.velocity += v1 + v2 + v3

        # Limit speed.
        boid.velocity = Vector(
            *limit_magnitude(boid.velocity, Boid.MIN_SPEED, Boid.MAX_SPEED))

        boid.position += boid.velocity * 0.1


def draw_boids(boids):
    pass


def setup():
    width = 600
    height = 600

    boids = [
        Boid(
            (random.uniform(0, width), random.uniform(0, height)),
            (random.uniform(-20, 20), random.uniform(-20, 20.0)),
        )
        for _ in range(60)
    ]

    return boids


def run():
    boids = setup()
    while True:
        draw_boids(boids)
        move_all_boids_to_new_positions(boids)


if __name__ == '__main__':
    # There is no visual for this, it simply checks the code runs.
    run()

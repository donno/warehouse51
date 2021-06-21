"""An attempt at using numpy to implement the boids algorithm as made famous by
C Reynolds in "Flocks, Herds, and Schools: A Distributed Behavioral Model"

The primarily source was:
    http://www.vergenet.net/~conrad/boids/pseudocode.html by Conrad Parker.
"""
import math
import numpy


def limit_magnitude(vector, min_magnitude, max_magnitude):
    mag = math.sqrt(sum(i ** 2 for i in vector))
    if mag > max_magnitude:
        normalizing_factor = max_magnitude / mag
    elif mag < min_magnitude:
        normalizing_factor = min_magnitude / mag
    else:
        return vector

    return vector * normalizing_factor


class Boids:
    # Speed limits to avoid the boids from moving too quickly and stopping.
    MIN_SPEED = 20.0
    MAX_SPEED = 180.0

    # This is used to determine the flockmates of a given boid also known as
    # the local neighbour hood. Often called the boid's perception.
    LOCAL_RANGE = 225.0  # Distance units.

    # This effects where a boid can see and thus where it can see its
    # flockmates (neighbours).
    VIEW_ANGLE = math.radians(110)

    def __init__(self, count, bounds=(500, 500)):
        generator = numpy.random.default_rng()

        # Initialise the positions.
        self.positions = generator.random((count, 2))
        self.positions[:, 0] *= bounds[0]
        self.positions[:, 1] *= bounds[1]

        # Initialise the velocities
        #
        # This is not intended to be -MAX_SPEED to MAX_SPEED but rather
        # -MAX_SPEED / 2 to MAX_SPEED / 2
        self.velocities = generator.random((count, 2)) * \
            Boids.MAX_SPEED - Boids.MAX_SPEED / 2

    def __len__(self):
        return self.positions.shape[0]

    def __iter__(self):
        for position, velocity in zip(self.positions, self.velocities):
            yield position, velocity

    def find_local_flockmates(self, index):
        """Find the flockmates that are near the boid at index. This is
        detonated by an array of true/false values stating which boids are
        consider flockmates.

        "The neighbourhood is characterized by a distance (measured from the
        center of the boid) and an angle, measured from the boid's direction
        of flight" - Craig Reynolds
        """

        # Compute the distance in each dimension between every boid.
        differences = boids.positions - boids.positions[index]

        # Could this avoid the square root? By squaring each element in
        # differences and comparing against a squared local range.
        distances = numpy.hypot(differences[:, 0], differences[:, 1])

        # Consider computing the speed of all the boids first. That way it can
        # be done in bulk.
        current_boid_speed = max(
            Boids.MIN_SPEED,
            math.sqrt(sum(i * i for i in boids.velocities[index])))

        current_boid_velocity_repeated = numpy.repeat(
            boids.velocities[index].reshape((1, 2)), boids.velocities.shape[0],
            axis=0)

        # Despite  numpy.dot() and numpy.vdot() neither will take two lists of
        # vectore, like so [a, b, c] and [d, e, f] and provide the resulting
        # array [dot(a, d), dot(b, e), dot(c, f)].
        #
        # I think I might be pushing my luck in hoping there was a way to do:
        # [dot(a, d), dot(a, e), dot(a, f)] when a is single item.
        dot_products = numpy.einsum(
            'ij,ij->i', boids.velocities, current_boid_velocity_repeated)

        # Adjust the distances the two arrays so there is no divide by zero
        # and no failure of arccos. The former is because hte distance from
        # the point to itself will be 0.0 and hte latter falls out when you
        # dot(a, a)
        dot_products[index] = 0.0
        distances[index] = 0.1
        #numpy.maximum(distances, 0.1, out=distances)

        # Determines the angle at which the boids are at relative to this
        # one.
        angles = numpy.arccos(
            numpy.clip(dot_products / (current_boid_speed * distances),
                       -1.0, 1.0))

        flockmate_mask = numpy.logical_and(distances < Boids.LOCAL_RANGE,
                                           angles < Boids.VIEW_ANGLE)

        # Don't consider a boid as a flockmate to itself.
        flockmate_mask[index] = False

        return flockmate_mask


def rule1(boids, current_boid_index, flockmates):
    """
    Rule 1: Boids try to fly towards the centre of mass of neighbouring boids.

    This is cohesion.
    """

    current_boid_position = boids.positions[current_boid_index]

    count = numpy.count_nonzero(flockmates)
    if count:
        # Computes the average position/ centroid of the flock.
        centre = boids.positions[flockmates].sum(axis=0) / count
        cohesion_vector = tuple(
            (avg - p) * 0.03 for avg, p in zip(centre, current_boid_position)
        )
    else:
        cohesion_vector = (0.0, 0.0)

    return cohesion_vector


def rule2(boids, current_boid_index, flockmates):
    """
    Rule 2: Boids try to keep a small distance away from other objects
    (including other boids).

    This is separation.
    """
    TOO_CLOSE_RANGE = 5.0

    current_boid_position = boids.positions[current_boid_index]

    c_x = 0.0
    c_y = 0.0

    # Compute the distance in each dimension between every boid.
    differences = boids.positions[flockmates] - current_boid_position

    distances = numpy.hypot(differences[:, 0], differences[:, 1])

    close_boids = distances < TOO_CLOSE_RANGE

    if close_boids.any():
        separation = (differences[close_boids] /
                      (distances[close_boids] ** 2)).sum(axis=0)
        numpy.subtract(numpy.zeros(separation.shape[0]), separation,
                       out=separation)
        return limit_magnitude(separation, 0.0, 1.0) * 7.5

    return numpy.zeros(2)


def rule3(boids, current_boid_index, flockmates):
    """
    Rule 3: Boids try to match velocity with near boids

    This is indirectly alignment as velocity is direction.
    """

    if not flockmates.any():
        # No nearby boids. maybe should fallback to using all of them.
        return (0.0, 0.0)

    velocity_x = 0.0
    velocity_y = 0.0

    velocity = boids.velocities[flockmates].sum(axis=0)
    flockmates_count = numpy.count_nonzero(flockmates)

    return velocity / flockmates_count * 0.045


def move_all_boids_to_new_positions(boids: Boids):
    for index in range(len(boids)):
        flockmates = boids.find_local_flockmates(index)

        v1 = rule1(boids, index, flockmates)
        v2 = rule2(boids, index, flockmates)
        v3 = rule3(boids, index, flockmates)

        boids.velocities[index] += v1 + v2 + v3

        # Limit the speed
        boids.velocities[index] = limit_magnitude(
            boids.velocities[index], Boids.MIN_SPEED, Boids.MAX_SPEED)

        boids.positions[index] += boids.velocities[index] * 0.1

def run():
    boids = Boids(100, bounds=(500, 500))
    for _ in range(100):
        move_all_boids_to_new_positions(boids)

if __name__ == '__main__':
    # There is no visual for this, it simply checks the code runs.
    boids = Boids(4, bounds=(10, 10))
    print(len(boids))
    assert len(boids) == 4
    print(boids.positions)

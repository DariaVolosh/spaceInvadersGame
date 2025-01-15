import json
from time import sleep
from lottie.objects import Animation
import pygame

pygame.init()

# Screen and basic initialization
display_info = pygame.display.Info()
screen_width = 1400 #display_info.current_w
screen_height = 700 #display_info.current_h
screen = pygame.display.set_mode((screen_width, screen_height))
pygame.display.set_caption("Space invaders")

# Player
player_bottom_padding = 0.025 * screen_height
player_image = pygame.image.load("images/space_fighter.png")
player_x = (screen_width - player_image.get_width()) / 2
player_y = screen_height - player_image.get_height() - player_bottom_padding
player_speed = 5
is_left_pressed = False
is_right_pressed = False

# Bullet
bullet_width = 20
bullet_height = 20
bullet_image = pygame.transform.scale(pygame.image.load("images/bullet.png"), (bullet_width, bullet_height))
bullet_x = 0
bullet_y = 0
bullet_speed = 10
is_bullet_fired = False

# Invader
invader_width = 60
invader_height = 60
invaders_padding = 30
invaders_row_padding = 25
invaders_rows = 2
invaders_rows_y = []
invaders_x = []
invader_speed = 1
# invaders_per_row calculated by using screen width, width of one invader and padding between invaders
# the relation between those values can be described as following equation
# screen_width = invader_width * invaders_amount + invaders_padding * (invaders_amount - 1) =>
# invaders_amount = (screen_width + invaders_padding) / (invader_width + invaders_padding)
invaders_per_row_float = (screen_width + invaders_padding) / (invader_width + invaders_padding)
invaders_per_row = int(invaders_per_row_float)
outside_padding = int(round(invaders_per_row_float - invaders_per_row, 2) * (invader_width + invaders_padding) / 2)

current_killed_invader_row = 0
current_killed_invader_index = 0

invaders = []
killed_invaders = []
moving_invaders = []
static_invaders = []
for row in range(invaders_rows):
    invaders_row = []
    x_row = []
    static_invaders_row = []

    for invader in range(invaders_per_row):
        static_invaders_row.append(invader)
        invader_image = pygame.transform.scale(pygame.image.load("images/space_invader.png"), (invader_width, invader_height))
        invaders_row.append(invader_image)
        if invader == 0:
            x_row.append(outside_padding)
        else:
            x_row.append(x_row[invader - 1] + invader_width + invaders_padding)

    if row == 0:
        invaders_rows_y.append(int(0.1 * screen_height))
    else:
        invaders_rows_y.append(invaders_rows_y[row-1] + invader_height + invaders_row_padding)

    invaders_x.append(x_row)
    invaders.append(invaders_row)
    static_invaders.append(static_invaders_row)
    killed_invaders.append([])
    moving_invaders.append([])


# Explosion
explosion_width = 50
explosion_height = 50
explosion_frames = [
    pygame.transform.scale(pygame.image.load("images/explosion_frame1.png"), (explosion_width, explosion_height)),
    pygame.transform.scale(pygame.image.load("images/explosion_frame2.png"), (explosion_width, explosion_height)),
    pygame.transform.scale(pygame.image.load("images/explosion_frame3.png"), (explosion_width, explosion_height)),
    pygame.transform.scale(pygame.image.load("images/explosion_frame4.png"), (explosion_width, explosion_height)),
    pygame.transform.scale(pygame.image.load("images/explosion_frame5.png"), (explosion_width, explosion_height)),
    pygame.transform.scale(pygame.image.load("images/explosion_frame6.png"), (explosion_width, explosion_height))
]

is_explosion_animation_in_progress = False
explosion_timer = 0
current_explosion_frame = 0
explosion_frame_time = 50

clock = pygame.time.Clock()

def reset_bullet_x():
    return (player_x + player_image.get_width() / 2) - bullet_image.get_width() / 2

def reset_bullet_y():
    return player_y - bullet_image.get_height()

bullet_x = reset_bullet_x()
bullet_y = reset_bullet_y()

# Time elapsed since last frame was shown
dt = 0

while True:
    for event in pygame.event.get():
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_LEFT:
                is_left_pressed = True
            elif event.key == pygame.K_RIGHT:
                print('right down')
                is_right_pressed = True
            elif event.key == pygame.K_SPACE:
                print('space down')
                is_bullet_fired = True
        elif event.type == pygame.KEYUP:
            if event.key == pygame.K_LEFT:
                print('left up')
                is_left_pressed = False
            elif event.key == pygame.K_RIGHT:
                print('right up')
                is_right_pressed = False

    screen.fill((0, 0, 0))

    for row in range(len(invaders)):
        for invader in range(len(invaders[row])):
            if invader not in killed_invaders[row]:
                screen.blit(invaders[row][invader], (invaders_x[row][invader], invaders_rows_y[row]))

    for row in range(len(moving_invaders)):
        for moving_invader_i in range(len(moving_invaders[row])):
            invader = moving_invaders[row][moving_invader_i][0]

            print("BEFOREEEEEEE")
            print(moving_invaders[row][moving_invader_i][0], "row:", row)
            print(moving_invaders)
            print(killed_invaders)
            print(static_invaders)

            # next invader, that the current invader collides with while moving to the right side
            # case 1 (row, current_moving_invader) < (row, static_invader) (NEXT COLLIDED INVADER) < (row, next_moving_invader) OR
            # case 2 (row, static_invader) < (row, current_moving_invader) < (row, next_moving_invader) (NEXT COLLIDED INVADER) < (row, next_static_invader)
            right_collided_invader = -1
            left_collided_invader = -1

            is_right_border_collided = False
            is_left_border_collided = False

            for i in range(invader+1, invaders_per_row):
                if i in static_invaders[row] or len(list(filter(lambda x: x[0] == i, moving_invaders[row]))) == 1:
                    right_collided_invader = i
                    break

            if invader+1 == invaders_per_row or all(num in killed_invaders[row] for num in range(invader+1, invaders_per_row)):
                is_right_border_collided = True

            for i in range(invader - 1, -1, -1):
                if i in static_invaders[row] or len(list(filter(lambda x: x[0] == i, moving_invaders[row]))) == 1:
                    left_collided_invader = i
                    break

            if invader-1 < 0 or all(num in killed_invaders[row] for num in range(invader-1, -1, -1)):
                is_left_border_collided = True

            direction_right = moving_invaders[row][moving_invader_i][1]

            print(left_collided_invader, moving_invaders[row][moving_invader_i][0], right_collided_invader)
            print("is moving right", direction_right)
            print("is right border collided", is_right_border_collided)
            print("is left border collided", is_left_border_collided)

            if direction_right:
                if is_right_border_collided:
                    #print(screen_width - outside_padding - invader_width, invaders_x[row][invader])
                    if screen_width - outside_padding - invader_width <= invaders_x[row][invader]:
                        moving_invaders[row][moving_invader_i][1] = False

                    invaders_x[row][invader] += invader_speed
                else:
                    if invaders_x[row][right_collided_invader] - invaders_x[row][invader] >= invaders_padding + invader_width:
                        invaders_x[row][invader] += invader_speed
                    else:
                        moving_invaders[row][moving_invader_i][1] = False

                        if right_collided_invader not in static_invaders[row]:
                            moving_invaders[row][moving_invader_i + 1][1] = True
            else:
                if is_left_border_collided:
                    if invaders_x[row][invader] <= outside_padding:
                        moving_invaders[row][moving_invader_i][1] = True

                    invaders_x[row][invader] -= invader_speed
                else:
                    if invaders_x[row][invader] - invaders_x[row][left_collided_invader] >= invaders_padding + invader_width:
                        invaders_x[row][invader] -= invader_speed
                    else:
                        moving_invaders[row][moving_invader_i][1] = True

                        if left_collided_invader not in static_invaders[row]:
                            moving_invaders[row][moving_invader_i - 1][1] = False


            #print("AFTERRRRRRR")
            #print(left_collided_invader, moving_invaders[row][moving_invader_i][0], right_collided_invader)
            #print("is moving right", moving_invaders[row][moving_invader_i][1])
            #print("is right border collided", is_right_border_collided)
            #print("is left border collided", is_left_border_collided)


    if is_left_pressed:
        player_x -= player_speed
    if is_right_pressed:
        player_x += player_speed

    if is_explosion_animation_in_progress:
        explosion_timer += dt
        if explosion_timer >= explosion_frame_time * (current_explosion_frame + 1):
            explosion_x = invaders_x[current_killed_invader_row][current_killed_invader_index] + (invader_width - explosion_width) / 2
            explosion_y = invaders_rows_y[current_killed_invader_row] + (invader_height - explosion_height) / 2
            screen.blit(explosion_frames[current_explosion_frame], (explosion_x, explosion_y))
            current_explosion_frame += 1

        if current_explosion_frame == len(explosion_frames):
            current_explosion_frame = 0
            is_explosion_animation_in_progress = False
            explosion_timer = 0


    if is_bullet_fired:
        screen.blit(bullet_image, (bullet_x, bullet_y))
        bullet_y -= bullet_speed
        if bullet_y <= invaders_rows_y[-1] + invader_height:
            #print("bullet x:", bullet_x)
            for row in range(len(invaders)):
                for invader in range(len(invaders[row])):
                    #print(row, invaders_x[row][invader_x])
                    #print(invaders_x[row][invader] <= bullet_x <= invaders_x[row][invader] + invader_width)
                    if (invaders_x[row][invader] <= bullet_x <= invaders_x[row][invader] + invader_width and
                            bullet_y <= invaders_rows_y[row] and invader not in killed_invaders[row]
                    ):
                        # current invader is being added to the list of killed invaders
                        killed_invaders[row].append(invader)

                        #print("BEFOREEE-----")
                        #print(row, invader)
                        #print(moving_invaders)
                        #print(killed_invaders)
                        #print(static_invaders)

                        # added left and right invader to the list of moving invaders, since they have the space
                        # between each other after killing the invader between them (if these invaders are not moving)

                        #print(len(list(filter(lambda x: print(x[0]), moving_invaders))))
                        #print(len(list(filter(lambda x: x[0] == (row, invader+1), moving_invaders))))

                        is_killed_invader_moving = list(filter(lambda x: x[0] == invader, moving_invaders[row]))
                        if (
                                invader + 1 < invaders_per_row and
                                invader - 1 >= 0 and
                                len(list(filter(lambda x: x[0] == invader - 1, moving_invaders[row]))) == 0 and
                                len(list(filter(lambda x: x[0] == invader+1, moving_invaders[row]))) == 0 and
                                len(is_killed_invader_moving) == 0 and
                                invader - 1 not in killed_invaders[row] and
                                invader + 1 not in killed_invaders[row]

                        ):
                            #print("condition true", invader - 1, invader+1)
                            moving_invaders[row].append([invader - 1, True])
                            moving_invaders[row].append([invader + 1, False])

                            # moving invaders (left and right one) and killed invader are being removed from list of
                            # static invaders
                            if invader - 1 in static_invaders[row]:
                                static_invaders[row].remove(invader - 1)

                            if invader + 1 in static_invaders[row]:
                                static_invaders[row].remove(invader + 1)


                        if len(is_killed_invader_moving) == 1:
                            moving_invaders[row].remove(is_killed_invader_moving[0])

                        if invader in static_invaders[row]:
                            static_invaders[row].remove(invader)

                        #print(row, invader)
                        #print(moving_invaders)
                        #print(killed_invaders)
                        #print(static_invaders)

                        #print(active_invaders)
                        is_bullet_fired = False
                        is_explosion_animation_in_progress = True
                        current_killed_invader_row = row
                        current_killed_invader_index = invader

                        for killed_row in range(len(killed_invaders)):
                            killed_invaders[killed_row].sort()

                        for moving_row in range(len(moving_invaders)):
                            moving_invaders[moving_row].sort()
                        break
                if not is_bullet_fired:
                    bullet_y = reset_bullet_y()
                    break

        if bullet_y <= 0:
            bullet_y = reset_bullet_y()
            is_bullet_fired = False
    else:
        bullet_x = reset_bullet_x()

    screen.blit(player_image, (player_x, player_y))
    pygame.display.flip()
    dt = clock.tick(60) # setting fps
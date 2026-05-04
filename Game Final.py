import pygame
import random
import math
import sys
import asyncio

# Initialize Pygame
pygame.init()

# Screen dimensions
SCREEN_WIDTH = 1000
SCREEN_HEIGHT = 600
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("100m Hurdle Race - Montclair State University")

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (200, 50, 50)
BROWN = (139, 90, 43)
ORANGE = (255, 140, 0)
BLUE = (50, 100, 200)
GREEN = (50, 150, 50)
YELLOW = (255, 220, 0)
GRAY = (150, 150, 150)
TRACK_RED = (180, 60, 60)
LANE_WHITE = (240, 240, 240)

# School colors
SCHOOL_COLORS = {
    "Montclair State": {"primary": (200, 50, 50), "secondary": WHITE},
    "Rowan": {"primary": (101, 67, 33), "secondary": (218, 165, 32)},
    "William Paterson": {"primary": (255, 140, 0), "secondary": BLACK},
    "Rutgers Newark": {"primary": (204, 0, 51), "secondary": GRAY},
    "NJCU": {"primary": (0, 100, 0), "secondary": (218, 165, 32)},
}

# Game constants
FPS = 60
GRAVITY = 0.8
JUMP_POWER = -14
GROUND_Y = 450
HURDLE_HEIGHT = 60
HURDLE_WIDTH = 15
NUM_HURDLES = 10
RACE_DISTANCE = 100  # meters
PIXELS_PER_METER = 80

# Fonts
font_large = pygame.font.Font(None, 72)
font_medium = pygame.font.Font(None, 48)
font_small = pygame.font.Font(None, 32)
font_tiny = pygame.font.Font(None, 24)


class Runner:
    def __init__(self, name, school, lane, is_player=False):
        self.name = name
        self.school = school
        self.lane = lane
        self.is_player = is_player
        self.x = 50
        self.y = GROUND_Y
        self.velocity_y = 0
        self.speed = 0
        self.max_speed = 8 if is_player else random.uniform(6.5, 7.8)
        self.distance = 0  # meters traveled
        self.is_jumping = False
        self.leg_phase = 0  # For running animation
        self.leg_speed = 0
        self.colors = SCHOOL_COLORS[school]
        self.finished = False
        self.finish_time = 0
        self.hurdle_penalty = 0
        self.penalty_timer = 0
        self.hit_hurdle = False

        # AI properties
        self.ai_reaction_distance = random.uniform(30, 50)
        self.ai_consistency = random.uniform(0.85, 0.98)

    def update(self, hurdles, current_time):
        if self.finished:
            return

        # Handle penalty slowdown
        if self.penalty_timer > 0:
            self.penalty_timer -= 1
            speed_reduction = 0.5
        else:
            speed_reduction = 1.0
            self.hit_hurdle = False

        if self.is_player:
            # Player speed based on leg movement
            self.speed = min(self.leg_speed * speed_reduction, self.max_speed)
        else:
            # AI movement
            self.ai_update(hurdles, speed_reduction)

        # Update position
        self.distance += self.speed * 0.016  # Convert to meters (roughly)

        # Update leg animation
        if self.speed > 0:
            self.leg_phase += self.speed * 0.15

        # Jumping physics
        if self.is_jumping:
            self.velocity_y += GRAVITY
            self.y += self.velocity_y

            if self.y >= GROUND_Y:
                self.y = GROUND_Y
                self.is_jumping = False
                self.velocity_y = 0

        # Check for finish
        if self.distance >= RACE_DISTANCE:
            self.finished = True
            self.finish_time = current_time
            self.distance = RACE_DISTANCE

    def ai_update(self, hurdles, speed_reduction):
        # AI running logic
        target_speed = self.max_speed * self.ai_consistency * speed_reduction

        # Gradually adjust speed
        if self.speed < target_speed:
            self.speed += 0.1
        else:
            self.speed = target_speed

        # AI jumping logic
        for hurdle in hurdles:
            hurdle_distance = hurdle.distance - self.distance
            if 0 < hurdle_distance * PIXELS_PER_METER < self.ai_reaction_distance:
                if not self.is_jumping and self.y >= GROUND_Y:
                    # Random chance to time jump poorly
                    if random.random() < self.ai_consistency:
                        self.jump()
                    break

    def jump(self):
        if not self.is_jumping and self.y >= GROUND_Y:
            self.is_jumping = True
            self.velocity_y = JUMP_POWER

    def apply_penalty(self):
        self.penalty_timer = 45  # frames of slowdown
        self.hit_hurdle = True
        self.hurdle_penalty += 1

    def get_screen_x(self, camera_offset):
        return 150  # Player stays centered, world moves

    def get_lane_y(self):
        return 200 + self.lane * 80

    def draw(self, screen, camera_offset):
        lane_y = self.get_lane_y()
        draw_y = lane_y + (self.y - GROUND_Y)
        draw_x = self.get_screen_x(camera_offset)

        # Adjust x based on distance difference from camera
        if not self.is_player:
            draw_x = 150 + (self.distance - camera_offset / PIXELS_PER_METER) * PIXELS_PER_METER

        if draw_x < -50 or draw_x > SCREEN_WIDTH + 50:
            return

        primary = self.colors["primary"]
        secondary = self.colors["secondary"]

        # Flash red if hit hurdle
        if self.hit_hurdle and self.penalty_timer % 10 < 5:
            primary = (255, 100, 100)

        # Body
        body_bob = math.sin(self.leg_phase) * 2 if self.speed > 0 and not self.is_jumping else 0

        # Torso
        pygame.draw.ellipse(screen, primary, (draw_x - 12, draw_y - 45 + body_bob, 24, 35))

        # Head
        pygame.draw.circle(screen, (210, 180, 140), (int(draw_x), int(draw_y - 55 + body_bob)), 12)

        # Arms (pumping motion)
        arm_swing = math.sin(self.leg_phase) * 25 if self.speed > 0 else 0
        arm_y = draw_y - 35 + body_bob
        # Left arm
        pygame.draw.line(screen, (210, 180, 140),
                         (draw_x - 8, arm_y),
                         (draw_x - 15 + arm_swing * 0.3, arm_y + 20 - abs(arm_swing) * 0.2), 4)
        # Right arm
        pygame.draw.line(screen, (210, 180, 140),
                         (draw_x + 8, arm_y),
                         (draw_x + 15 - arm_swing * 0.3, arm_y + 20 - abs(arm_swing) * 0.2), 4)

        # Legs (running animation)
        leg_swing = math.sin(self.leg_phase) * 30 if self.speed > 0 else 0
        leg_y = draw_y - 12 + body_bob

        # Left leg
        left_leg_x = draw_x - 6 + leg_swing * 0.4
        left_foot_y = draw_y + 5 - abs(math.sin(self.leg_phase)) * 15
        pygame.draw.line(screen, secondary, (draw_x - 6, leg_y), (left_leg_x, left_foot_y), 5)

        # Right leg
        right_leg_x = draw_x + 6 - leg_swing * 0.4
        right_foot_y = draw_y + 5 - abs(math.cos(self.leg_phase)) * 15
        pygame.draw.line(screen, secondary, (draw_x + 6, leg_y), (right_leg_x, right_foot_y), 5)

        # Shoes
        pygame.draw.circle(screen, primary, (int(left_leg_x), int(left_foot_y)), 5)
        pygame.draw.circle(screen, primary, (int(right_leg_x), int(right_foot_y)), 5)

        # School name above runner
        name_text = font_tiny.render(self.school.split()[0], True, BLACK)
        screen.blit(name_text, (draw_x - name_text.get_width() // 2, draw_y - 80))
class Hurdle:
    def __init__(self, distance, lane=None):
        self.distance = distance  # in meters
        self.lane = lane  # None means all lanes
        self.knocked = [False] * 5  # Track if knocked by each runner

    def get_screen_x(self, camera_offset):
        return self.distance * PIXELS_PER_METER - camera_offset + 150

    def draw(self, screen, camera_offset, lane):
        x = self.get_screen_x(camera_offset)
        if x < -50 or x > SCREEN_WIDTH + 50:
            return

        lane_y = 200 + lane * 80

        # Hurdle color (orange/black stripes)
        if not self.knocked[lane]:
            # Vertical posts
            pygame.draw.rect(screen, ORANGE, (x - 2, lane_y - HURDLE_HEIGHT + 5, 4, HURDLE_HEIGHT - 5))
            pygame.draw.rect(screen, ORANGE, (x + HURDLE_WIDTH - 2, lane_y - HURDLE_HEIGHT + 5, 4, HURDLE_HEIGHT - 5))

            # Top bar with stripes
            for i in range(5):
                color = ORANGE if i % 2 == 0 else WHITE
                pygame.draw.rect(screen, color,
                                 (x + i * (HURDLE_WIDTH // 5), lane_y - HURDLE_HEIGHT, HURDLE_WIDTH // 5 + 1, 8))
        else:
            # Knocked hurdle (tilted)
            pygame.draw.polygon(screen, ORANGE, [
                (x, lane_y - 10),
                (x + 30, lane_y - 15),
                (x + 35, lane_y),
                (x + 5, lane_y)
            ])

    def check_collision(self, runner, runner_index):
        if self.knocked[runner_index]:
            return False

        runner_distance = runner.distance
        hurdle_start = self.distance - 0.3
        hurdle_end = self.distance + 0.3

        # Check if runner is at hurdle position
        if hurdle_start <= runner_distance <= hurdle_end:
            jump_height = GROUND_Y - runner.y
            if jump_height < HURDLE_HEIGHT - 10:  # Not jumping high enough
                return True
        return False


class Game:
    def __init__(self):
        self.state = "start"  # start, countdown, running, finished
        self.reset_game()

    def reset_game(self):
        # Create runners
        self.runners = []
        schools = list(SCHOOL_COLORS.keys())

        # Player is always Montclair State in lane 2 (middle)
        self.player = Runner("Player", "Montclair State", 2, is_player=True)
        self.runners.append(self.player)

        # AI runners
        other_schools = [s for s in schools if s != "Montclair State"]
        lanes = [0, 1, 3, 4]
        for i, lane in enumerate(lanes):
            school = other_schools[i]
            runner = Runner(f"Runner {i + 1}", school, lane, is_player=False)
            self.runners.append(runner)

        # Create hurdles (standard 100m hurdle positions)
        self.hurdles = []
        hurdle_positions = [13, 22, 31, 40, 49, 58, 67, 76, 85, 94]
        for pos in hurdle_positions:
            self.hurdles.append(Hurdle(pos))

        self.camera_offset = 0
        self.timer = 0
        self.countdown = 3
        self.countdown_timer = 0
        self.leg_alternate = 0
        self.race_started = False
        self.keys_pressed = {"left": False, "right": False}

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False

            if event.type == pygame.KEYDOWN:
                if self.state == "start":
                    if event.key == pygame.K_SPACE:
                        self.state = "countdown"
                        self.countdown_timer = pygame.time.get_ticks()

                elif self.state == "running":
                    if event.key == pygame.K_SPACE:
                        self.player.jump()
                    elif event.key == pygame.K_LEFT:
                        if not self.keys_pressed["left"]:
                            self.keys_pressed["left"] = True
                            if self.leg_alternate != 1:
                                self.player.leg_speed = min(self.player.leg_speed + 2, self.player.max_speed)
                                self.leg_alternate = 1
                    elif event.key == pygame.K_RIGHT:
                        if not self.keys_pressed["right"]:
                            self.keys_pressed["right"] = True
                            if self.leg_alternate != 2:
                                self.player.leg_speed = min(self.player.leg_speed + 2, self.player.max_speed)
                                self.leg_alternate = 2

                elif self.state == "finished":
                    if event.key == pygame.K_SPACE:
                        self.reset_game()
                        self.state = "start"

            if event.type == pygame.KEYUP:
                if event.key == pygame.K_LEFT:
                    self.keys_pressed["left"] = False
                elif event.key == pygame.K_RIGHT:
                    self.keys_pressed["right"] = False

        return True

    def update(self):
        if self.state == "countdown":
            elapsed = (pygame.time.get_ticks() - self.countdown_timer) / 1000
            self.countdown = 3 - int(elapsed)
            if self.countdown <= 0:
                self.state = "running"
                self.timer = 0
                self.race_started = True

        elif self.state == "running":
            self.timer += 1 / FPS

            # Decrease player speed over time (need to keep pressing)
            self.player.leg_speed = max(0, self.player.leg_speed - 0.05)

            # Update all runners
            for runner in self.runners:
                runner.update(self.hurdles, self.timer)

            # Check collisions
            for hurdle in self.hurdles:
                for i, runner in enumerate(self.runners):
                    if hurdle.check_collision(runner, i):
                        hurdle.knocked[i] = True
                        runner.apply_penalty()

            # Update camera to follow player
            self.camera_offset = self.player.distance * PIXELS_PER_METER

            # Check if all runners finished
            if all(runner.finished for runner in self.runners):
                self.state = "finished"

    def draw_track(self):
        # Sky
        screen.fill((135, 206, 235))

        # Stadium background
        pygame.draw.rect(screen, (100, 100, 100), (0, 100, SCREEN_WIDTH, 100))
        pygame.draw.rect(screen, (80, 80, 80), (0, 150, SCREEN_WIDTH, 50))

        # Draw crowd (simple dots)
        for i in range(200):
            x = (i * 7 + int(self.camera_offset * 0.1)) % SCREEN_WIDTH
            y = 110 + (i % 4) * 10
            color = random.choice([RED, BLUE, YELLOW, WHITE, GREEN]) if i % 20 == 0 else (
                random.randint(50, 100), random.randint(50, 100), random.randint(50, 100)
            )
            pygame.draw.circle(screen, color, (x, y), 3)

        # Track surface
        pygame.draw.rect(screen, TRACK_RED, (0, 180, SCREEN_WIDTH, 420))

        # Lane lines
        for i in range(6):
            y = 200 + i * 80 - 40
            pygame.draw.line(screen, LANE_WHITE, (0, y), (SCREEN_WIDTH, y), 2)

        # Distance markers
        for meter in range(0, 101, 10):
            x = meter * PIXELS_PER_METER - self.camera_offset + 150
            if 0 <= x <= SCREEN_WIDTH:
                pygame.draw.line(screen, WHITE, (x, 180), (x, 580), 2)
                text = font_tiny.render(f"{meter}m", True, WHITE)
                screen.blit(text, (x - 10, 560))

        # Start line
        start_x = 0 * PIXELS_PER_METER - self.camera_offset + 150
        if 0 <= start_x <= SCREEN_WIDTH:
            pygame.draw.line(screen, WHITE, (start_x, 180), (start_x, 580), 4)

        # Finish line
        finish_x = 100 * PIXELS_PER_METER - self.camera_offset + 150
        if 0 <= finish_x <= SCREEN_WIDTH:
            # Checkered pattern
            for i in range(20):
                for j in range(5):
                    color = WHITE if (i + j) % 2 == 0 else BLACK
                    pygame.draw.rect(screen, color, (finish_x + (i % 2) * 10, 200 + j * 80 - 35, 10, 20))

    def draw_hud(self):
        # Timer
        timer_text = font_medium.render(f"Time: {self.timer:.2f}s", True, BLACK)
        pygame.draw.rect(screen, WHITE, (10, 10, timer_text.get_width() + 20, 50), border_radius=10)
        screen.blit(timer_text, (20, 20))

        # Distance
        distance_text = font_small.render(f"Distance: {self.player.distance:.1f}m / 100m", True, BLACK)
        pygame.draw.rect(screen, WHITE, (10, 70, distance_text.get_width() + 20, 40), border_radius=10)
        screen.blit(distance_text, (20, 78))

        # Speed bar
        speed_pct = self.player.speed / self.player.max_speed
        pygame.draw.rect(screen, WHITE, (SCREEN_WIDTH - 220, 10, 210, 50), border_radius=10)
        pygame.draw.rect(screen, GRAY, (SCREEN_WIDTH - 210, 25, 180, 20), border_radius=5)
        pygame.draw.rect(screen,
                        GREEN if speed_pct > 0.7 else YELLOW if speed_pct > 0.3 else RED,
                        (SCREEN_WIDTH - 210, 25, int(180 * speed_pct), 20),
                        border_radius=5)
        speed_label = font_tiny.render("SPEED", True, BLACK)
        screen.blit(speed_label, (SCREEN_WIDTH - 150, 5))

        # Penalties
        if self.player.hurdle_penalty > 0:
            penalty_text = font_small.render(f"Hurdle Hits: {self.player.hurdle_penalty}", True, RED)
            pygame.draw.rect(screen, WHITE, (10, 120, penalty_text.get_width() + 20, 35), border_radius=10)
            screen.blit(penalty_text, (20, 125))

        # Controls
        controls = font_tiny.render("← → = Run | SPACE = Jump", True, WHITE)
        screen.blit(controls, (SCREEN_WIDTH // 2 - controls.get_width() // 2, SCREEN_HEIGHT - 30))

        # Position
        positions = sorted(self.runners, key=lambda r: r.distance, reverse=True)
        player_pos = positions.index(self.player) + 1
        pos_text = font_medium.render(f"Position: {player_pos}/5", True, BLACK)
        pygame.draw.rect(screen, WHITE, (SCREEN_WIDTH - 220, 70, 210, 50), border_radius=10)
        screen.blit(pos_text, (SCREEN_WIDTH - 210, 80))

    def draw_start_screen(self):
        screen.fill((50, 50, 80))

        title = font_large.render("100m HURDLE RACE", True, WHITE)
        screen.blit(title, (SCREEN_WIDTH // 2 - title.get_width() // 2, 100))

        subtitle = font_medium.render("Montclair State University", True, RED)
        screen.blit(subtitle, (SCREEN_WIDTH // 2 - subtitle.get_width() // 2, 180))

        instructions = [
            "CONTROLS:",
            "",
            "← → Arrow Keys: Alternate to run faster",
            "SPACEBAR: Jump over hurdles",
            "",
            "TIME YOUR JUMPS! Hitting hurdles slows you down.",
            "",
            "Press SPACE to start"
        ]

        for i, line in enumerate(instructions):
            color = YELLOW if i == 0 else WHITE
            text = font_small.render(line, True, color)
            screen.blit(text, (SCREEN_WIDTH // 2 - text.get_width() // 2, 280 + i * 35))

        pygame.draw.ellipse(screen, RED, (SCREEN_WIDTH // 2 - 12, 520, 24, 35))
        pygame.draw.circle(screen, (210, 180, 140), (SCREEN_WIDTH // 2, 495), 12)

    def draw_countdown(self):
        self.draw_track()

        for runner in self.runners:
            runner.draw(screen, self.camera_offset)

        for hurdle in self.hurdles:
            for lane in range(5):
                hurdle.draw(screen, self.camera_offset, lane)

        if self.countdown > 0:
            count_text = font_large.render(str(self.countdown), True, WHITE)
            pygame.draw.circle(screen, BLACK, (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2), 60)
            pygame.draw.circle(screen, RED, (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2), 55)
            screen.blit(count_text, (SCREEN_WIDTH // 2 - count_text.get_width() // 2,
                                    SCREEN_HEIGHT // 2 - count_text.get_height() // 2))
        else:
            go_text = font_large.render("GO!", True, GREEN)
            screen.blit(go_text, (SCREEN_WIDTH // 2 - go_text.get_width() // 2,
                                    SCREEN_HEIGHT // 2 - go_text.get_height() // 2))

    def draw_finished_screen(self):
        self.draw_track()

        for runner in self.runners:
            runner.draw(screen, self.camera_offset)

        overlay = pygame.Surface((500, 400))
        overlay.set_alpha(240)
        overlay.fill((30, 30, 50))
        screen.blit(overlay, (SCREEN_WIDTH // 2 - 250, 100))

        title = font_medium.render("RACE COMPLETE!", True, YELLOW)
        screen.blit(title, (SCREEN_WIDTH // 2 - title.get_width() // 2, 120))

        rankings = sorted(self.runners, key=lambda r: r.finish_time)
        for i, runner in enumerate(rankings):
            color = YELLOW if i == 0 else WHITE
            if runner.is_player:
                color = (100, 255, 100) if i == 0 else (100, 200, 255)

            place = ["1st", "2nd", "3rd", "4th", "5th"][i]
            text = f"{place}: {runner.school} - {runner.finish_time:.2f}s"
            if runner.hurdle_penalty > 0:
                text += f" ({runner.hurdle_penalty} hits)"
            rank_text = font_small.render(text, True, color)
            screen.blit(rank_text, (SCREEN_WIDTH // 2 - rank_text.get_width() // 2, 180 + i * 45))

        player_rank = rankings.index(self.player)
        if player_rank == 0:
            message = "CONGRATULATIONS! YOU WON!"
            msg_color = YELLOW
        else:
            message = f"You finished in {['1st', '2nd', '3rd', '4th', '5th'][player_rank]} place"
            msg_color = WHITE

        msg_text = font_medium.render(message, True, msg_color)
        screen.blit(msg_text, (SCREEN_WIDTH // 2 - msg_text.get_width() // 2, 420))

        restart = font_small.render("Press SPACE to play again", True, WHITE)
        screen.blit(restart, (SCREEN_WIDTH // 2 - restart.get_width() // 2, 470))

    def draw(self):
        if self.state == "start":
            self.draw_start_screen()
        elif self.state == "countdown":
            self.draw_countdown()
        elif self.state == "running":
            self.draw_track()

            # Draw hurdles
            for hurdle in self.hurdles:
                for lane in range(5):
                    hurdle.draw(screen, self.camera_offset, lane)

            # Draw runners
            for runner in sorted(self.runners, key=lambda r: r.lane):
                runner.draw(screen, self.camera_offset)

            self.draw_hud()

        elif self.state == "finished":
            self.draw_finished_screen()

        pygame.display.flip()

# -------------------------------
# ASYNC MAIN LOOP FOR PYGBAG
# -------------------------------

async def main():
    global game
    game = Game()

    running = True
    clock = pygame.time.Clock()

    while running:
        running = game.handle_events()
        game.update()
        game.draw()

        clock.tick(FPS)
        await asyncio.sleep(0)  # required for pygbag browser loop

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    asyncio.run(main())

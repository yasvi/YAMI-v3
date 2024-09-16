import pygame
import librosa as lbr
from random import choice
import cv2                
import numpy as np

class BeatsGame:
    def __init__(self):
        pygame.init()
        
        # Game settings
        self.width = 800
        self.height = 600
        self.fall_speed = 5  # Pixels per animation frame
        self.endline_y = self.height - 80  # Y position for the endline
        self.tolerance = 50  # Tolerance in pixels before and after the endline
        
        # Colors
        self.white = (255, 255, 255)
        self.red = (255, 0, 0)
        self.black = (0, 0, 0)
        self.green = (0, 255, 0)  
        
        # Initialize display
        self.screen = pygame.display.set_mode((self.width, self.height))
        pygame.display.set_caption('YAMI')
        
        # Allow player to select the video
        self.video_options = ['bg2.mov', 'bg3.mp4', 'bg4.mov']
        self.video_path = self.select_video()  
        self.video = cv2.VideoCapture(self.video_path)
        self.frame_rate = self.video.get(cv2.CAP_PROP_FPS)
        self.frame_time = int(1000 / self.frame_rate)
        
        # Load audio
        self.audio_path = 'After_dark.mp3'
        self.y, self.sr = lbr.load(self.audio_path)
        self.harmonic, self.percussive = lbr.effects.hpss(self.y)
        
        # Increase hop length or adjust lag for onset sensitivity
        onset_env = lbr.onset.onset_strength(y=self.percussive, sr=self.sr, hop_length=512, lag=1)

        # Detect beats and smooth them
        self.tempo, _ = lbr.beat.beat_track(onset_envelope=onset_env, sr=self.sr)
        self.beat_frames, self.beat_indices = lbr.beat.beat_track(onset_envelope=onset_env, sr=self.sr)
        self.beat_time = lbr.frames_to_time(self.beat_indices, sr=self.sr)

        # Apply smoothing to remove irregular beats
        self.beat_time = self.filter_major_beats(self.beat_time)

        # Additional smoothing using simple moving average
        self.beat_time = self.smooth_beats(self.beat_time)

        duration = len(self.y) / self.sr
        print(duration)
        
        #print("Filtered beats:", self.beat_time)

        # Initialize Pygame mixer
        pygame.mixer.init()
        pygame.mixer.music.load(self.audio_path)
        pygame.mixer.music.play(-1)
        
        self.beats = []  # To keep track of beats
        self.start_time = pygame.time.get_ticks()
        self.score = 0  # Initialize score
        
        # Initialize video
        # background = choice(['bg2.mov','bg3.mp4','bg4.mov'])
        # print(background)
        # self.video_path = (background)
        # self.video = cv2.VideoCapture(self.video_path)
        # self.frame_rate = self.video.get(cv2.CAP_PROP_FPS)
        # self.frame_time = int(1000 / self.frame_rate)
        
        # Run the game
        self.run_game()
        
    def select_video(self):
        """Display a menu for the user to select a video."""
        running = True
        while running:
            self.screen.fill(self.black)
            font = pygame.font.Font(None, 36)
            text = font.render("Select a Background Video (1-3):", True, self.white)
            self.screen.blit(text, (200, 100))

            for i, option in enumerate(self.video_options, start=1):
                option_text = font.render(f"{i}. {option}", True, self.white)
                self.screen.blit(option_text, (200, 150 + 50 * i))

            pygame.display.flip()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    quit()
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_1:
                        return self.video_options[0]
                    elif event.key == pygame.K_2:
                        return self.video_options[1]
                    elif event.key == pygame.K_3:
                        return self.video_options[2]
                    
    def filter_major_beats(self, beat_times):
        if len(beat_times) < 2:
            return beat_times  # Not enough beats to filter

        # Calculate the average beat interval
        intervals = [beat_times[i+1] - beat_times[i] for i in range(len(beat_times)-1)]
        avg_interval = sum(intervals) / len(intervals)

        # Filter beats that are close to the average interval
        filtered_beats = [beat_times[0]]  # Start with the first beat
        for i in range(1, len(beat_times)):
            if abs(beat_times[i] - filtered_beats[-1] - avg_interval) < avg_interval * 0.5:
                filtered_beats.append(beat_times[i])
        
        return filtered_beats
    
    def smooth_beats(self, beat_times):
        smoothed_beats = []
        window_size = 3  # Adjust the window size for more smoothing
        for i in range(len(beat_times) - window_size):
            avg_time = sum(beat_times[i:i+window_size]) / window_size
            smoothed_beats.append(avg_time)
        return smoothed_beats


    def create_beat(self):
        column_x = choice([100, 350, 600])  # Randomly select a column
        beat_rect = pygame.Rect(column_x, 0, 50, 20)
        self.beats.append(beat_rect)
        #print(f"Beat created at column: {column_x}")

    def animate_beats(self):
        for beat in self.beats:
            beat.y += self.fall_speed
            if beat.y > self.height:
                self.beats.remove(beat)

    def draw_beats(self):
        for beat in self.beats:
            pygame.draw.rect(self.screen, self.white, beat)
    
    def draw_endline(self):
        pygame.draw.line(self.screen, self.green, (0, self.endline_y), (self.width, self.endline_y), 2)
    
    def draw_score(self):
        font = pygame.font.Font(None, 36)  # Use default font and size 36
        score_text = font.render(f"Score: {self.score}", True, self.white)
        self.screen.blit(score_text, (10, 10))  # Draw score in the top-left corner

    def draw_background(self):
        #Draw the selected video as background 
        ret, frame = self.video.read()
        if ret:
            frame = cv2.resize(frame, (self.width, self.height))
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            frame = np.transpose(frame, (1, 0, 2))
            frame = pygame.surfarray.make_surface(frame)
            self.screen.blit(frame, (0, 0))
        else:
            self.video.set(cv2.CAP_PROP_POS_FRAMES, 0)

    def run_game(self):
        running = True
        clock = pygame.time.Clock()
        beat_index = 0
        
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key in [pygame.K_a, pygame.K_s, pygame.K_d]:
                        self.handle_key(event.key)
            
            current_time = pygame.time.get_ticks() / 1000  # Convert milliseconds to seconds
            
            # Check if we need to create a new beat
            if beat_index < len(self.beat_time) and current_time >= self.beat_time[beat_index]:
                self.create_beat()
                beat_index += 1
            
            self.draw_background()
            self.animate_beats()
            self.draw_beats()
            self.draw_endline()  # Draw the endline
            self.draw_score()    # Draw the score
            pygame.display.flip()
            clock.tick(60)
        
        pygame.quit()
        self.video.release()

    def handle_key(self, key):
        column_x = {pygame.K_a: 100, pygame.K_s: 350, pygame.K_d: 600}.get(key)
        if column_x is not None:
            for beat in self.beats:
                if (beat.x == column_x and
                    self.endline_y - self.tolerance <= beat.y <= self.endline_y + self.tolerance):  # Tolerance zone
                    self.beats.remove(beat)
                    self.score += 1  # Increase score for a successful hit
                    break

if __name__ == "__main__":
    BeatsGame()

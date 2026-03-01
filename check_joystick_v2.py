import pygame
import sys
import time

def check_joystick():
    pygame.init()
    pygame.joystick.init()

    # --- Window Setup (Optional but good for focus) ---
    WIDTH, HEIGHT = 400, 300
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Joystick Tester")
    
    font = pygame.font.SysFont("Arial", 20)

    print("====================================")
    print("      Joystick Diagnosis Tool       ")
    print("====================================")
    print("1. Connect your controller.")
    print("2. Press buttons or move axes.")
    print("3. Watch the console for ID numbers.")
    print("====================================")

    # Wait for joystick
    while pygame.joystick.get_count() == 0:
        print("Waiting for joystick...", end='\r')
        pygame.event.pump()
        time.sleep(0.5)
        # Allow exit
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                sys.exit()
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                sys.exit()
    
    print("\nJoysticks detected:")
    for i in range(pygame.joystick.get_count()):
        js = pygame.joystick.Joystick(i)
        js.init()
        print(f"ID {i}: {js.get_name()} (Instance ID: {js.get_instance_id()})")
        print(f"    Buttons: {js.get_numbuttons()}")
        print(f"    Axes:    {js.get_numaxes()}")
        print(f"    Hats:    {js.get_numhats()}")

    print("\nStarting Event Loop. Press CTRL+C or Close Window to exit.")
    
    running = True
    while running:
        screen.fill((0, 0, 0))
        text_surface = font.render("Press buttons to see IDs in console", True, (255, 255, 255))
        screen.blit(text_surface, (20, 100))
        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                running = False

            elif event.type == pygame.JOYBUTTONDOWN:
                print(f"[BUTTON DOWN] Joystick: {event.joy} | Button ID: {event.button}")
            
            elif event.type == pygame.JOYBUTTONUP:
                print(f"[BUTTON UP  ] Joystick: {event.joy} | Button ID: {event.button}")
            
            elif event.type == pygame.JOYAXISMOTION:
                # Filter small noise
                if abs(event.value) > 0.1: 
                     print(f"[AXIS MOVE  ] Joystick: {event.joy} | Axis ID: {event.axis} | Value: {event.value:.2f}")

            elif event.type == pygame.JOYHATMOTION:
                print(f"[HAT MOVE   ] Joystick: {event.joy} | Hat ID: {event.hat} | Value: {event.value}")
                
            elif event.type == pygame.JOYDEVICEADDED:
                print(f"[DEVICE ADDED] New joystick connected")
                
            elif event.type == pygame.JOYDEVICEREMOVED:
                print(f"[DEVICE REMOVED] Joystick disconnected")

    pygame.quit()

if __name__ == "__main__":
    check_joystick()

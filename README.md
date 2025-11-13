# Pedestrian-Traffic-Light-System
This project implements a smart pedestrian-crossing traffic light with adaptive timing, audible feedback, LCD display messages, and vehicle-violation detection.

## Main Features

### Pedestrian Button Logic

- When the pedestrian button is pressed, the system emits an audible confirmation beep.

- After the button press, the pedestrian traffic light waits between 10 and 60 seconds before switching to green.

- This time depends on the current vehicle traffic flow:
-- Higher traffic flow → longer waiting time

-- Lower traffic flow → shorter waiting time

### Pedestrian Light Activation

- When the pedestrian light switches to green:

- A sound signal is emitted.

- The LCD display shows a message informing that it is safe to cross.

- The LCD also displays a countdown timer indicating how long remains before the light changes.

### Adaptive Audible Signaling

- While the pedestrian light is green, the system emits periodic beeps.

- The beep frequency increases as the green phase ends, helping visually impaired users estimate the remaining time.

- The green-light duration ranges from 10 to 40 seconds, depending on traffic conditions:

- Higher traffic flow → shorter pedestrian-green time

- Lower traffic flow → longer pedestrian-green time

### Red-Light Violation Detection

- If a vehicle crosses during the red light:

- A photo is automatically captured.

- A variable named fines is incremented.

- The updated fine count is displayed on the LCD.

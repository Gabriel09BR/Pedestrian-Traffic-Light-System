# Pedestrian-Traffic-Light-System
This project implements a smart pedestrian-crossing traffic light with adaptive timing, audible feedback, LCD display messages, and vehicle-violation detection.

## Main Features

### Pedestrian Button Logic

- When the pedestrian button is pressed, the system emits an audible confirmation beep.

- After the button press, the pedestrian traffic light waits between 10 and 60 seconds before switching to green.

- This time depends on the current vehicle traffic flow:
  - Higher traffic flow → longer waiting time

  - Lower traffic flow → shorter waiting time

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

  - A LED flashes to simulate a photo capture (no real image is taken).

  - A variable named fines is incremented.

  ## 🚗 Traffic Flow Measurement

In this prototype, the traffic flow is simulated using a potentiometer connected to an analog input, which is mapped to a normalized flow value (0.0–1.0). This flow level affects:

- The waiting time before the pedestrian light turns green (10–60 seconds)
- The duration of the pedestrian green phase (10–40 seconds)

In a real system, traffic flow could be measured using:

- An infrared barrier to count vehicles
- An ultrasonic sensor to detect vehicle presence and occupancy time
- Magnetic or inductive sensors embedded in the pavement
- A computer vision system using a camera

The measured flow is then converted into a normalized value used by the controller logic.


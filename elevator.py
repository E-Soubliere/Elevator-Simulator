"""Elevator algorithm simulation program.

automated elevator simulation written for SmartCone Technologies Inc.
Program simulates a building with 3 elevators which calculates the most
optimal path to pick up passengers, and distributes passengers giving the
shortest possible wait time.

"""

#Imports
import time
import threading
import random
import os

CLEAR = 'cls' if os.name == 'nt' else 'clear'

#Elevator directions
UP = 1
DOWN = -1
#Building variables, max floors and total number of elevators
NUM_OF_FLOORS = 12
NUM_OF_ELEVATORS = 3

#Global time scale, smaller numbers give quicker simulation results
TIME_SCALE = 0.05

#Decides the method of choosing an elevator. 0 = random, 1 = calculated
METHOD = 1  

class Elevator:
    """Elevator which reponds to floor request

    Manages movement and transportation of passengers, accepts floor requests and
    orders the request optimally, based on direction. Keeps track of all riders currently
    aboard or waiting for the elevator.

    Args:
        floor_count (int): total number of floors
        floor (int): starting floor. Defaults to 1
        Direction (int): starting vertical direction of the elevator. Defaults to UP

    Attributes:
        floor (int): The evelator's current floor
        floor_count (int): Total number of elevator floors
        direction (int): direction of travel
        queue (list): List of queued floors
        riders (list): List of all riders currently queued for travel
    """
    def __init__(self, floor_count, floor=1, direction=UP):
        self.floor = floor
        self.floor_count = floor_count
        self.direction = UP
        self.queue = list()
        self.riders = list()
    def request(self, floor):
        """Adds the floor to the list of queued floors

        If the floor is valid, and not already queued, adds the floor to the queue 

        Args:
            floor (int): floor number to request for travel

        Return:
            bool: false if floor requested is out of range
        """
        #return for floors out of range
        if floor < 1 or floor > self.floor_count: return False
        #add floor to queue if it's not already
        if floor not in self.queue:
            #print(f"{floor} requested")
            self.queue.append(floor)

    def move(self):
        """Moves the elevator in it's current direction

        Checks if the elevator has any queued floors, then moves one floor towards that floor.
        Determines the direction of travel based on the next queued floor each move before traveling.
        If the floor reached is a queued floor, visit the floor for passenger departure and arrival.
        
        """
        #while the queue is not empty, move towards next requested floor
        if len(self.queue) > 0:
            self.setDirection()
            self.floor += self.direction

            #If the elevator is on the next requested floor, visit the floor
            if self.floor == self.queue[0]:
                return self.visit()
        return False 

    def visit(self):
        """add or remove riders who requested the current floor

        checks for riders who are boarded who have arrived at their destination floor and
        removes them from the rider list. Checks for riders who are not boarded and arrived at their starting floor
        and adds their destination floor to the queue. Calculates wait time for all boarding
        passengers. Recalculates direction and returns a list of all passengers who boarded this floor.

        Returns:
            list: all passengers who boarded on this floor

        """
        boarded = list()
        #remove riders who requested this floor or request destination of riders entering
        for rider in self.riders:
            #riders who are boarded and reached destination
            if self.floor == rider.destination and rider.boarded:
                self.riders.remove(rider)
            #riders who are not boarded yet and arrived at starting floor
            elif self.floor == rider.start and not rider.boarded:
                rider.boarded = True
                rider.wait_time = time.time() - rider.wait_time
                boarded.append(rider)
                self.request(rider.destination)

        #Remove current floor from the list
        self.queue.remove(self.floor)

        #Determine new direction based on next floor in the queue
        self.setDirection()

        return boarded

    def setDirection(self):
        """Calculate new direction of elevator

        Check for next floor in the queue and recalculate direction based on its relation to the
        current floor. If no floors in the queue, don't change direction

        """

        if len(self.queue) > 0:
            if self.queue[0] > self.floor:
                self.direction = UP
            else:
                self.direction = DOWN

    def sortQueue(self):
        """Sorts queue in best order for travel

        Based on current direction, orders queue ascending if UP or descending if DOWN
        then continues to append the first floor of the queue to the end of the queue if it
        is in the opposite direction of the current floor and direction of elevator.
        Continues in current direction as long as there are queued floors in that direction

        """
        if len(self.queue) == 1: return
        if self.direction == UP:
            self.queue.sort()
            while (self.queue[0] < self.floor):
                self.queue.append(self.queue.pop(0))
        else:
            self.queue.sort(reverse=True)
            while (self.queue[0] > self.floor):
                self.queue.append(self.queue.pop(0))


class Passenger:
    """A passenger of an elevator
    
    used to request starting and ending floors of an elevator and keep track of
    time waiting for elevator arrival

    Attributes:
        start (int): starting floor
        destination (int): destination floor
        wait_time (float): total time waiting for elevator arrival
        boarded (bool): boarding status, true is passenger has boarded the elevator, false otherwise
    """
    def __init__(self):
        self.start = random.randint(1, NUM_OF_FLOORS)
        self.destination = random.randint(1, NUM_OF_FLOORS)
        self.wait_time = 0
        self.boarded = False

        #recalculate destination if it is the same as the starting floor
        while self.destination == self.start:
            self.destination = random.randint(0, NUM_OF_FLOORS)

    def getDirection(self):
        """Gets the passenger's direction of travel

        Determines direction based on destination in relation to the start floor

        Returns:
            int for direction

        """
        if self.start > self.destination:
            return DOWN
        else:
            return UP

    
class Building:
    """Building object which holds elevators and passengers

    maintains a set number of elevators and runs them continuously, records passenger wait times
    and total trips completed. Decides which elevator a passenger should take and sends their floor requests
    to the elevators queue

    Attributes:
        floors (int): total number of floors
        elevators (list): list of elevators in the building
        completed (int): total number of passengers who arrived on the elevator
        total_wait_time (float): total time waited for initial floor requests of all passengers
    """
    def __init__(self, num_of_elevators, num_of_floors):
        self.floors = num_of_floors
        self.elevators = list()
        self.completed = 0
        self.total_wait_time = 0
        for i in range(num_of_elevators):
            self.elevators.append(Elevator(num_of_floors))

    def addRider(self, rider):
        """Adds a rider to an elevator queue

        Chooses an elevator based on the prefered method (Method 0 = random, method 1 = calculated)
        and adds the rider to that elevator queue. Saves the current time when the rider is queued,
        used later to calculate total time waited

        Args:
            rider (obj): a Rider object to be appended into an elevator's queue of riders

        """
        #determine which elevator to send the rider on
        e = self.chooseBestElevator(rider, METHOD)

        #add rider to the list of riders
        e.riders.append(rider)
        
        #Start wait timer
        rider.wait_time = time.time()
        #request the elevator to the rider's starting floor
        e.request(rider.start)


    def chooseBestElevator(self, rider, method=0):
        """Chooses the best elevator for the given rider, given the method

        Method 0 choose an elevator at random

        method 2 ranks each elevator by distancefrom the rider's starting floor and chooses
        the closest one

        Args:
            rider (obj): Rider to determine which elevator to append to
            method (int): method of determining which elevator to choose. Default to 0 (random)

        Return:
            Elevator Object for the chosen rider
        """

        #method 0: chooses elevator by random
        if method == 0:
            return self.elevators[random.randint(0, len(self.elevators)-1)]

        #method 2: chooses best possible elevator
        if method == 1:
            #pick the closest elevator
            best = self.elevators[0]
            for e in self.elevators:
                if self.getDistance(e, rider) < self.getDistance(best, rider):
                    best = e

            return best

    def getDistance(self, elevator, rider):
        """Determines the distance between the elevator and the rider's start floor

        Calculates distance based on direction and queue. if the elevator is moving towards the rider,
        calculate the difference between the elevator and rider. if the elevator is moving away
        from the rider, calculate the difference between the elevator and its max/min queued floor, then add the difference
        between the max/min floor to the rider.

        Args:
            elevator (obj): elevator to calculate the distance from
            rider (obj): rider to calculate the distance to
        
        Return:
            int of total distance from elevator to rider
        """

        if len(elevator.queue) == 0:
            return abs(elevator.floor - rider.start)
        elif elevator.direction == UP and elevator.floor > rider.start:
            #find distance to highest floor, then add distance from highest to rider start
            return abs(max(elevator.queue) - elevator.floor + max(elevator.queue) - rider.start)
        elif elevator.direction == DOWN and elevator.floor < rider.start:
            return abs(min(elevator.queue) - elevator.floor + min(elevator.queue) - rider.start)
        else:
            return abs(elevator.floor - rider.start)
                

    def run(self):
        """begins run functionality for building and moves each elevator every tick

        moves each elevator in the building eavy tick. if the elevator returns any riders,
        add rider's wait times to total wait time and increment the completed by one.
        Print out a visual representation of the elevators and wait for 1 tick

        """
        while True:
            for e in self.elevators:
                riders = e.move()
                if riders != False:
                    for rider in riders:
                        self.total_wait_time += rider.wait_time
                        self.completed += 1
            self.printStatus()
            time.sleep(1*TIME_SCALE)

    def printStatus(self):
        """Prints a visual respresentation of the elevators and statistics

        clears console and prints out a horizontal bar in relation to the elevators current floor,
        followed by the floor number, and a list of all floors currently queued.
        Prints total number of passengers who have made it onto the elevator and the average
        time it took for the elevator to reach them.

        """
        #clear console
        os.system(CLEAR)   
        for e in self.elevators:
            #print each elevator
            print("\u2588" * e.floor * 2, end=" ")
            print(f"[{e.floor}] {e.queue}")
        #print statistics
        print(f"Completed Trips: {self.completed}")
        print(f"Average Wait Time: {self.getAverageTime()}")

    def getAverageTime(self):
        """calculates average time waited based on total time wated and total start requests completed
        
        Return:
            float for average time

        """
        #avoid division by 0
        if self.completed > 0:
            return self.total_wait_time / self.completed


#initializes the building with NUM_OF_ELEVATORS, and FLOORS
b = Building(NUM_OF_ELEVATORS, NUM_OF_FLOORS)

#begins Thread for building run function, constantly moving the elevators while the programs randomly adds passangers
t = threading.Thread(target=b.run)
t.start()

while True:
    #waits for a random amount of time between 5 and 10 seconds (scaled via global TIME_SCALE) and adds a new random passenger
    time.sleep(random.randint(5, 10)*TIME_SCALE)
    b.addRider(Passenger())
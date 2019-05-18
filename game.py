import threading
import pygame

pygame.init()
win = pygame.display.set_mode((500, 500))
font = pygame.font.SysFont('comicsans', 80)
clock = pygame.time.Clock()


class GameThread(threading.Thread):
    def __init__(self, thread_id, name, count):
        threading.Thread.__init__(self)
        self.thread_id = thread_id
        self.name = name
        self.count = count

    def run(self):
        print('Starting: ' + self.name + "\n")
        x = font.render(str(self.thread_id), 1, (255, 255, 255))
        while self.count:
            clock.tick(30)
            win.fill((0, 255, 0))
            print(self.name, self.count, '\n')
            self.count -= 1
            win.blit(x, (100, 100))
            pygame.display.update()

        print('Exiting ' + self.name + "\n")


def go():
    thread1 = MyThread(1, "MyThread 1", 20)
    thread2 = MyThread(2, "MyThread 2", 20)

    thread1.start()
    thread2.start()
    thread1.join()
    thread2.join()
    print("Done")

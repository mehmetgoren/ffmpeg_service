from threading import Thread


def start_thread(target, args):
    th = Thread(target=target, args=args)
    th.daemon = True
    th.start()

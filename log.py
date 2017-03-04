# author: Samuel Wejeus (samuel@isalldigital.com)

__DEBUG = True


def debug(message):
    if __DEBUG:
        print "DEBUG: " + message


def error(message):
    print "ERROR: {0}".format(message)


def info(message):
    print message

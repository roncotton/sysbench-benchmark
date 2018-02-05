#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Deep Learning Research - WSU Vancouver

# machine_bench.py
# -----------------
# Requires: sysbench, python 3.x
# outputs machine info and runs sysbench CPU and FileIO benchmark for
# determining baseline performance on system.

# installing sysbench
# debian/ubuntu:
# sudo apt-get install sysbench

# MacOSX
# brew install sysbench

# Windows10
# install Windows Feature - Linux Subsystem
# sudo apt-get install sysbench

# other articles about sysbench
# http://imysql.com/wp-content/uploads/2014/10/sysbench-manual.pdf
# https://anothermysqldba.blogspot.com/2013/05/benchmarking-mysql-cpu-file-io-memory.html
# http://blog.siphos.be/2013/04/comparing-performance-with-sysbench-part-2/

import platform             # for computerInfo() method
import socket               # for computerInfo() method
import subprocess           # for executing script
import multiprocessing      # to define # of threads
import sys                  # needed for file io
import os                   # making a directory
import errno                # error
import time                 # time differences
import shutil               # deleting directory
import datetime             # timestamp

# globals
num_tests = 10
home_directory = os.getcwd()
temp_dir = "/tmp"
benchmark_dir = home_directory + "/machine-benchmarks"
temp_path = benchmark_dir + temp_dir
machine_specs = benchmark_dir + "/machine-specs.txt"
machine_modules_local = benchmark_dir + "/python-local-modules.txt"
machine_modules_virtualenv = benchmark_dir + "/python-virtualenv-modules.txt"
machine_sysbench_cpu = benchmark_dir + "/machine-sysbench-cpu.txt"
machine_sysbench_memory = benchmark_dir + "/machine-sysbench-memory.txt"
machine_sysbench_threads = benchmark_dir + "/machine-sysbench-threads.txt"
machine_sysbench_file = benchmark_dir + "/machine-sysbench-file.txt"
file_first_run = True

argt = "--num-threads=" + str(multiprocessing.cpu_count())

# --- Info

def computerInfo(save=False, filename=machine_specs):
    '''platform independent machine information
    first boolean argument determines if stdout is saving
    second argument determines filename output'''
    fqdn = socket.getfqdn()
    hostname = socket.gethostname()
    if save:
        orig_stdout = sys.stdout
        f = open(filename, 'w')
        sys.stdout = f
    print(platform.python_implementation(), platform.python_build()[0])
    print(platform.platform())
    print(platform.machine(), platform.processor(),
          "x", multiprocessing.cpu_count(), "cores")
    print("FQDN:", platform.node(), "(", fqdn, ")")
    print("LAN IPv4:", socket.gethostbyname(hostname))
    # more network info
    # print("IPv6/IPv4: ", socket.getaddrinfo(hostname, None))
    if save:
        sys.stdout = orig_stdout
        f.close()

def pythonModules(arg='', filename=machine_modules_local):
    with open(filename, "a") as output:
        subprocess.call(["pip", "list", "--format=columns", arg], stdout=output)

# --- Benchmarks

def sysbenchCPU(prime=20000, filename=machine_sysbench_cpu):
    '''execute sysbench cpu benchmark
    sysbench --test=cpu --cpu-max-prime=xxxxxxx --num-threads=xxx run'''
    arg1 = "--cpu-max-prime=" + str(prime)
    # argt is crutial for utilization of all cores
    with open(filename, "a") as output:
        subprocess.call(["sysbench", "--test=cpu", arg1, argt, "run"], stdout=output)


def sysbenchMemory(
    mem_block_size='1K',
    mem_total_size='10G',
     filename=machine_sysbench_memory):
    '''benchmark for memory
    sysbench --test=memory --memory-block-size=xxx --memory-total-size=xxx --num-threads=xxx run'''
    arg1 = "--memory-block-size=" + mem_block_size
    arg2 = "--memory-total-size=" + mem_total_size
    # argt is crutial for utilization of all cores
    with open(filename, "a") as output:
        subprocess.call(["sysbench", "--test=memory", arg1,
                        arg2, argt, "run"], stdout=output)


def sysbenchThreads(num_threads=128, max_time='10s',filename=machine_sysbench_threads):
    '''benchmark for threads
    sysbench --test=threads --num-threads=xxx --max-time=xxx run
    Note: --num-threads > number of cores'''
    arg1 = "--num-threads=" + str(num_threads)
    arg2 = "--max-time=" + max_time
    # argt is crutial for utilization of all cores
    with open(filename, "a") as output:
        subprocess.call(["sysbench", "--test=threads",
                        arg1, arg2, "run"], stdout=output)


def sysbenchFile(i, file_total_size='10G', filename=machine_sysbench_file):
    '''benchmark for fileio - ran in tmp folder
    sysbench --test=fileio --file-total-size=xxx prepare
    sysbench --test=fileio --file-test-mode=rndrw --file-total-size=xxx --num-threads=xxx run
    sysbench --test=fileio --file-total-size=xxx cleanup'''
    arg1 = "--file-total-size=" + file_total_size
    global file_first_run, num_tests

    if file_first_run:
        os.chdir(benchmark_dir)
        createDirectory()
        os.chdir(temp_path)
        devnull = open(os.devnull, "w")
        subprocess.call(["sysbench",
            "--test=fileio", "--file-test-mode=rndrw", arg1, "prepare"], stdout=devnull)
        devnull.close()
        file_first_run = False
    # argt is crutial for utilization of all cores
    os.chdir(temp_path)
    with open(filename, "a") as output:
        subprocess.call(["sysbench",
                        "--test=fileio", "--file-test-mode=rndrw", arg1, argt, "run"], stdout=output)
    if i == num_tests:
        devnull = open(os.devnull, "w")
        subprocess.call(["sysbench",
                        "--test=fileio", "--file-test-mode=rndrw", arg1, "cleanup"], stdout=devnull)
        devnull.close()
        os.chdir('..')
        deleteDirectory(temp_path)
    os.chdir(benchmark_dir)

# --- Directory Manipulation


def createDirectory(directory='tmp'):
    '''if the directory doesn't exist, create'''
    if not os.path.exists(directory):
        os.makedirs(directory)


def deleteDirectory(directory='tmp'):
    '''if directory exists, delete files and directory'''
    if os.path.isdir(directory):
        shutil.rmtree(benchmark_dir)

# --- File Manipulation


def deleteFile(filename):
    '''if the file exists, delete file'''
    if os.path.isfile(filename):  # this checks only for files, not dirs
        os.remove(filename)


def fileSysout(filename=''):
    '''output file to stdout'''
    try:
        f = open(filename, 'r')
    except IOError:
        print("Error: File not found to output.")
    else:
        with f:
            print(f.read())
    f.close()


def appendLine(filename='', text=''):
    '''append a single line of text to file'''
    with open(filename, "a") as f:
        f.write(text)

def pauseTest(timeoutsec=1):
    time.sleep(timeoutsec)

# --- MAIN ---


def main():
    '''executes computer_info() and sysbench
    '''

    deleteDirectory(benchmark_dir)              # create direcory structure
    createDirectory(benchmark_dir)

    computerInfo(True)                            # save computer info into file

    print("Computer Info Complete")

    pythonModules()
    pythonModules('--local', machine_modules_virtualenv)

    print("Python Module Listing Complete")

    # CPU Test
    for i in range(num_tests):
        print("CPU Test:", (i + 1), "/", num_tests, "complete.")
        appendLine(machine_sysbench_cpu, "CPU Test " + str(i) + " Start: " + str(datetime.datetime.now()) + "\n")
        sysbenchCPU()		# standard test
        appendLine(machine_sysbench_cpu, "CPU Test " + str(i) + " End: " + str(datetime.datetime.now()) + "\n")
        pauseTest()

    # Memory Test
    for i in range(num_tests):
        print("Memory Test:", (i + 1), "/", num_tests, "complete.")
        appendLine(machine_sysbench_memory, "Memory Test " + str(i) + " Start: " + str(datetime.datetime.now()) + "\n")
        sysbenchMemory()	# standard test
        appendLine(machine_sysbench_memory, "Memory Test " + str(i) + " End: " + str(datetime.datetime.now()) + "\n")
        pauseTest()

    # Thread Test
    for i in range(num_tests):
        print("Thread Test:", (i + 1), "/", num_tests, "complete.")
        appendLine(machine_sysbench_threads, "Thread Test " + str(i) + " Start: " + str(datetime.datetime.now()) + "\n")
        sysbenchThreads()	# standard test
        appendLine(machine_sysbench_threads, "Thread Test " + str(i) + " End: " + str(datetime.datetime.now()) + "\n")
        pauseTest()

    # File Test
    # Note: if a more extensive test of IO is required, MySQL tests can be run using --test=oltp
    for i in range(num_tests):
        print("File Test:", (i + 1), "/", num_tests, "complete.")
        if i!=1:
            appendLine(machine_sysbench_file, "File Test " + str(i) + " Start: " + str(datetime.datetime.now()) + "\n")
        sysbenchFile(i,'16GB')                            # lowered size
        if i!=1:
            appendLine(machine_sysbench_file, "File Test " + str(i) + " End: " + str(datetime.datetime.now()) + "\n")
        pauseTest()

    # print results of tests
    fileSysout(machine_specs)                   # output results
    fileSysout(machine_modules_local)
    fileSysout(machine_modules_virtualenv)
    fileSysout(machine_sysbench_cpu)
    fileSysout(machine_sysbench_memory)
    fileSysout(machine_sysbench_threads)
    fileSysout(machine_sysbench_file)

if __name__ == "__main__":
    main()

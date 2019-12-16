#!/usr/bin/env python
from __future__ import absolute_import, division, print_function

import os
import subprocess
import time
import webbrowser

from six.moves import input

try:
    from urllib.request import Request, urlopen
    from urllib.error import URLError
except ImportError:
    from urllib2 import Request, urlopen
    from urllib2 import URLError


def verify_docker_install():
    try:
        subprocess.check_output(
            "docker info --format '{{.ServerVersion}}'".split())
        return True
    except OSError:
        return False


def test_install(port, token, counter=0):
    try:
        url = 'http://localhost:{}/alpr'.format(port)
        req = Request(url)
        req.get_method = lambda: 'POST'
        req.add_header('Authorization', 'Token {}'.format(token))
        res = urlopen(req).read()
        return True
    except:
        if counter < 20:
            time.sleep(2)
            counter +=1
            return test_install(port, token, counter=counter)
        else:
            return False  

def get_container_id(image):
        cmd = 'docker ps -q --filter ancestor={}'.format(image)
        output = subprocess.check_output(cmd.split())
        return output.decode()

def test_existing_install(image):
    image_id = get_container_id(image)
    if image_id:
        print(
            '\nYou already have a running platerecognizer daemon, Please Upgrade instead.'
        )
        exit(1)


def install(image,
            auto_start_container,
            port,
            token,
            license_key,
            extra_args='',
            docker_version='docker',
            image_version='latest'):
    test_existing_install(image)
    pull_cmd = 'docker pull {}:{}'.format(image, image_version)
    os.system(pull_cmd)
    run_cmd = '{} run --rm -t {} {} -p {}:8080 -v license:/license -e TOKEN={} -e LICENSE_KEY={} {}'.format(
        docker_version,
        "--restart unless-stopped" if auto_start_container else '',
        extra_args,
        port,
        token,
        license_key,
        image,
    )
    os.system(run_cmd)
    if test_install(port, token):
        print("\nInstallation successfull")
    else:
        print("\nInstallation was not successfull")

    print("\nUse the command below to run the sdk again.")
    print(run_cmd)


def get_image():
    images = subprocess.check_output(
        "docker images --format '{{.Repository}}' platerecognizer/alpr*".split(
        )).decode().split('\n')
    return images[0].replace("'", "")


def verify_token(token, license_key):
    try:
        req = Request('https://app.platerecognizer.com/v1/sdk-webhooks/{}/'.format(license_key))
        req.add_header('Authorization', 'Token {}'.format(token))
        res = urlopen(req).read()
        return True
    except URLError as e:
        if '404' in e:
            print('License Key is incorrect!!')
            return False
        elif '403' in e:
            print('Api Token is incorrect!!')
            return False    
        return False


def get_token_input():

    token = str(input('\nType your Token > '))
    license_key = str(input('Type your License Key > '))

    if not token or not license_key or not verify_token(token, license_key):
        print(
            "Invalid Token or License Key, get  license_key from https://app.platerecognizer.com/accounts/plan/"
        )
        webbrowser.open('https://app.platerecognizer.com/accounts/plan/')
        time.sleep(1)
        return get_token_input()
    else:
        return token, license_key


def stop_container(image):
    cmd = 'docker ps -q --filter ancestor={}'.format(image)
    container_id = subprocess.check_output(cmd.split())
    if container_id:
        cmd = 'docker stop {}'.format(container_id)
        os.system(cmd)
    return container_id


def main():

    if not verify_docker_install():
        print(
            "Docker is not installed, Follow 'https://docs.docker.com/v17.09/engine/installation/' to install docker for your hardware"
        )
        webbrowser.open('https://docs.docker.com/v17.09/engine/installation/')
        time.sleep(1)
        exit(1)

    actions = ('Install', 'Update', 'Uninstall', 'Quit')
    action_choice = 1

    for ind, choice in enumerate(actions):
        print("{}) {}".format(ind + 1, choice))
    while True:
        choice = int(input("Pick an action [default=1]:  > ") or 1)
        if choice == 4:
            print("Quit!")
            exit(1)
        if choice in [1, 2, 3]:
            action_choice = choice
            break
        else:
            print('Incorrect Choice')

    if action_choice == 1:
        hardwares = ('Intel CPU', 'Raspberry', 'GPU (Nvidia Only)',
                     'Jetson Nano', 'Quit')
        hardware = 1
        print('\n')
        for ind, choice in enumerate(hardwares):
            print("{}) {}".format(ind + 1, choice))
        while True:

            choice = int(
                input("What is the hardware of this machine [default=1] > ") or
                1)

            if choice == 4:
                print("Quit!")
                exit(1)
            if choice in [1, 2, 3, 4]:
                hardware = choice
                break
            else:
                print('Incorrect Choice')

        token, license_key = get_token_input()

        auto_start_container = False
        port = 8080
        print("\n1) Automatically start the container on boot")
        print("2) Continue")

        image = None

        while True:
            choice = int(input('Pick an action [default=2] > ') or 2)
            if choice in [1, 2]:
                if choice == 1:
                    auto_start_container = True
                break
            print('Incorrect choice')

        port = int(input('\nSet the container port [default=8080] > ') or 8080)

        print("\nStarting Installation")

        if hardware == 1:
            image = 'platerecognizer/alpr'
            install(image, auto_start_container, port, token, license_key)

        elif hardware == 2:
            image = 'platerecognizer/alpr-raspberry-pi'
            install(image, auto_start_container, port, token, license_key)

        elif hardware == 3:
            image = 'platerecognizer/alpr-gpu'
            install(image,
                    auto_start_container,
                    port,
                    token,
                    license_key,
                    extra_args='--runtume nvidia')

        elif hardware == 4:
            image = 'platerecognizer/alpr-jetson'
            install(image,
                    auto_start_container,
                    port,
                    token,
                    license_key,
                    extra_args='--runtume nvidia',
                    docker_version='nvidia-docker')

        exit(1)

    elif action_choice == 2:
        version = str(
            input('Which version would you like to install? [default=latest]')
            or 'latest')
        token, license_key = get_token_input()
        image = get_image()
        if not image:
            print(
                'PlateRecognizer SDK is not installed, Please select Install. Quitting!!'
            )
            exit(1)
        stop_container(image)
        extra_args = ''
        docker_version = 'docker'
        if 'jetson' in image:
            extra_args = '--runtume nvidia'
            docker_version = 'nvidia-docker'
        elif 'gpu' in image:
            extra_args = '--runtume nvidia'

        auto_start_container = False
        install(image,
                auto_start_container,
                8080,
                token,
                license_key,
                extra_args=extra_args,
                docker_version=docker_version,
                image_version=version)

    elif action_choice == 3:

        image = get_image()
        print(image)
        if not image:
            print(
                'PlateRecognizer SDK is not installed, Please select Install. Quitting!!'
            )
            exit(1)

        print(
            '\n1) Uninstall the SDK. You can then install it on another machine.'
        )
        print('2) Uninstall the SDK and remove the container.')
        print('3) Quit')
        while True:
            uninstall_choice = int(input('Pick an action [defaut=3] > ') or 3)
            if uninstall_choice in [1, 2, 3]:
                if uninstall_choice == 3:
                    print('Quitting!!')
                    exit(1)
                break

        token, license_key = get_token_input()
        if uninstall_choice == 1:
            stop_container(image)
            cmd = 'docker run --rm -t -v license:/license -e TOKEN={} -e UNINSTALL=1 {}'.format(
                token, image)
            os.system(cmd)

        elif uninstall_choice == 2:
            container_id = stop_container(image)
            cmd = 'docker run --rm -t -v license:/license -e TOKEN={} -e UNINSTALL=1 {}'.format(token, image)
            os.system(cmd)
            if container_id:
                cmd = 'docker container rm {}'.format(container_id)
                os.system(cmd)
            cmd = 'docker rmi "{}"'.format(image)
            os.system(cmd)  
            print('Uninstall complete!!')


if __name__ == "__main__":
    main()

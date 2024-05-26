class DRIVER:
    FS = None
    BLOCK_SIZE = 1024
    MAX_FILE_NAME_LENGTH = 15

    class File_system:
        def __init__(self, descriptors_max_num):
            self.descriptors_max_num = descriptors_max_num
            self.descriptors_num = 0
            self.descriptors = []
            self.descriptorsBitmap = [0 for i in range(descriptors_max_num)]
            self.Blocks = {}
            self.opened_files_num_descriptors = []
            self.opened_files = []

    class Descriptor:
        def __init__(self, num, file_type, length, name):
            self.NUM = num
            self.TYPE = file_type
            self.links_num = 1
            self.length = length
            self.blocks = []
            self.name = name
            self.links = [self]

        def show_info(self):
            print('%4d  %10s  %5d  %10d  %6d  %s' % (
            self.NUM, self.TYPE, self.links_num, self.length, len(self.blocks), self.name))

    class Link:
        def __init__(self, descriptor, name):
            descriptor.links_num += 1
            self.descriptor = descriptor
            self.name = name

        def show_info(self):
            print('%4d  %10s  %5d  %10d  %6d  %s' % (
            self.descriptor.NUM, self.descriptor.TYPE, self.descriptor.links_num, self.descriptor.length,
            len(self.descriptor.blocks), f'{self.name}->{self.descriptor.name}'))

    class Opened_file:
        def __init__(self, descriptor):
            if isinstance(descriptor, DRIVER.Link):
                self.descriptor = descriptor.descriptor
            else:
                self.descriptor = descriptor
            num_desc = 0
            while num_desc in DRIVER.FS.opened_files_num_descriptors:
                num_desc += 1
            DRIVER.FS.opened_files_num_descriptors.append(num_desc)
            self.num_descriptor = num_desc
            self.offset = 0


def mkfs(n):
    if DRIVER.FS is not None:
        print('Already initialised')
        return
    if not type(n) is int:
        print('n - int')
        return
    DRIVER.FS = DRIVER.File_system(n)
    print('Initialised')


def stat(name):
    if DRIVER.FS is None:
        print('FS is not initialised')
        return
    for descriptor in DRIVER.FS.descriptors:
        if descriptor.name == name:
            print('   №        type  links      length  blocks  name')
            descriptor.show_info()
            return
    print(f'Incorrect name')


def ls():
    if DRIVER.FS is None:
        print('FS is not initialised')
        return
    print('   №        type  links      length  blocks  name')
    for descriptor in DRIVER.FS.descriptors:
        descriptor.show_info()


def create(name):
    if DRIVER.FS is None:
        print('FS is not initialised')
        return
    if len(str(name)) > DRIVER.MAX_FILE_NAME_LENGTH:
        print(f'File name is too large')
    if DRIVER.FS.descriptors_num >= DRIVER.FS.descriptors_max_num:
        print('All descriptors are in use')
        return
    for descriptor in DRIVER.FS.descriptors:
        if descriptor.name == name:
            print('Incorrect name')
            return
    descriptor_num = None
    for i, value in enumerate(DRIVER.FS.descriptorsBitmap):
        if not value:
            DRIVER.FS.descriptorsBitmap[i] = 1
            descriptor_num = i
            break
    descriptor = DRIVER.Descriptor(descriptor_num, 'regular', 0, name)
    DRIVER.FS.descriptors.append(descriptor)
    DRIVER.FS.descriptors_num += 1
    print('   №        type  links      length  blocks  name')
    descriptor.show_info()


def link(name1, name2):
    if DRIVER.FS is None:
        print('FS is not initialised')
        return
    if len(str(name2)) > DRIVER.MAX_FILE_NAME_LENGTH:
        print(f'File name is too large')
    for descriptor in DRIVER.FS.descriptors:
        if descriptor.name == name2:
            print(f'Incorrect name2')
            return
    for descriptor in DRIVER.FS.descriptors:
        if descriptor.name == name1:
            new_link = DRIVER.Link(descriptor, name2)
            descriptor.links.append(new_link)
            DRIVER.FS.descriptors.append(new_link)
            print('   №        type  links      length  blocks  name')
            new_link.show_info()
            return
    print(f'Incorrect name1')


def unlink(name):
    if DRIVER.FS is None:
        print('FS is not initialised')
        return
    for descriptor in DRIVER.FS.descriptors:
        if descriptor.name == name:
            if isinstance(descriptor, DRIVER.Descriptor):
                print(f'Incorrect name')
                return
            else:
                descriptor.descriptor.links_num -= 1
                DRIVER.FS.descriptors.remove(descriptor)
                print('Link deleted')
                return
    print(f'Incorrect name')


def open(name):
    if DRIVER.FS is None:
        print('FS is not initialised')
        return
    for descriptor in DRIVER.FS.descriptors:
        if descriptor.name == name:
            openedFile = DRIVER.Opened_file(descriptor)
            DRIVER.FS.opened_files.append(openedFile)
            print(f'Done. id = {openedFile.num_descriptor}')
            return
    print(f'Incorrect name')


def close(fd):
    if DRIVER.FS is None:
        print('FS is not initialised')
        return
    if fd in DRIVER.FS.opened_files_num_descriptors:
        DRIVER.FS.opened_files_num_descriptors.remove(fd)
        for openedFile in DRIVER.FS.opened_files:
            if openedFile.num_descriptor == fd:
                DRIVER.FS.opened_files.remove(openedFile)
                del openedFile
                print(f'File closed')
                return
    print(f'Incorrect id')


def seek(fd, offset):
    if DRIVER.FS is None:
        print('FS is not initialised')
        return
    if fd not in DRIVER.FS.opened_files_num_descriptors:
        print(f'Incorrect id')
        return
    for openedFile in DRIVER.FS.opened_files:
        if openedFile.num_descriptor == fd:
            openedFile.offset = offset
            print('Offset is set')
            return


def write(fd, size, val):
    if DRIVER.FS is None:
        print('FS is not initialised')
        return
    if len(str(val)) != 1:
        print('val == 1 byte')
        return
    if fd not in DRIVER.FS.opened_files_num_descriptors:
        print(f'Incorrect id')
        return
    for openedFile in DRIVER.FS.opened_files:
        if openedFile.num_descriptor == fd:
            num = len(openedFile.descriptor.blocks)
            while openedFile.offset + size > num * DRIVER.BLOCK_SIZE:
                openedFile.descriptor.blocks.append(['\0' for i in range(DRIVER.BLOCK_SIZE)])
                num += 1
            num = 0
            for i in range(openedFile.offset + size):
                if i == DRIVER.BLOCK_SIZE * num + DRIVER.BLOCK_SIZE:
                    num += 1
                if i >= openedFile.offset:
                    openedFile.descriptor.blocks[num][i - num * DRIVER.BLOCK_SIZE] = val
            if openedFile.descriptor.length < openedFile.offset + size:
                openedFile.descriptor.length = openedFile.offset + size
            print('Data is written')
            return


def read(fd, size):
    if DRIVER.FS is None:
        print('FS is not initialised')
        return
    if fd not in DRIVER.FS.opened_files_num_descriptors:
        print(f'Incorrect id')
        return
    for openedFile in DRIVER.FS.opened_files:
        if openedFile.num_descriptor == fd:
            if openedFile.descriptor.length < openedFile.offset + size:
                print(f'Incorrect length')
                return
            num = openedFile.offset // DRIVER.BLOCK_SIZE
            answer = ""
            for i in range(openedFile.offset, openedFile.offset + size):
                if i == DRIVER.BLOCK_SIZE * num + DRIVER.BLOCK_SIZE:
                    num += 1
                answer += str(openedFile.descriptor.blocks[num][i - num * DRIVER.BLOCK_SIZE])
            print(answer)


def truncate(name, size):
    if DRIVER.FS is None:
        print('FS is not initialised')
        return
    for descriptor in DRIVER.FS.descriptors:
        if descriptor.name == name:
            if size < descriptor.length:
                num = len(descriptor.blocks)
                while num * DRIVER.BLOCK_SIZE > size + DRIVER.BLOCK_SIZE:
                    descriptor.blocks.pop(num - 1)
                    num -= 1
                descriptor.length = size
            if size > descriptor.length:
                num = len(descriptor.blocks) - 1
                for i in range(descriptor.length, size):
                    if i == DRIVER.BLOCK_SIZE * num + DRIVER.BLOCK_SIZE:
                        descriptor.blocks.append(['\0' for i in range(DRIVER.BLOCK_SIZE)])
                        num += 1
                    descriptor.blocks[num][i - num * DRIVER.BLOCK_SIZE] = 0
                descriptor.length = size
            print(f'File is truncated')
            return
    print(f'Incorrect name')


if __name__ == '__main__':
    while True:
        try:
            ans = input('~ ')
            ans = ans.split(' ')
            eval(f'{ans[0]}({",".join(ans[1:])})')
        except:
            print('Error!')

class DRIVER:
    FS = None
    cwd = None
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
            rootDescriptor = DRIVER.Descriptor(0, 'directory', 0, '/')
            rootDescriptor.links_num -= 1
            self.descriptors.append(rootDescriptor)
            self.descriptors_num += 1
            self.descriptorsBitmap[0] = 1
            rootDirectory = DRIVER.Directory('/', rootDescriptor, None)
            self.root = rootDirectory
            DRIVER.cwd = rootDirectory

    class Descriptor:
        def __init__(self, num, file_type, length, name, content=None):
            self.NUM = num
            self.TYPE = file_type
            self.links_num = 1
            self.length = length
            self.blocks = []
            self.name = name
            self.links = [self]
            if file_type == 'symlink':
                self.content = content

        def show_info(self):
            if self.TYPE == 'symlink':
                printname = f'{self.name}->{self.content}'
            else:
                printname = self.name
            print('%4d  %10s  %5d  %10d  %6d  %s' % (self.NUM, self.TYPE, self.links_num, self.length, len(self.blocks), printname))

    class Link:
        def __init__(self, descriptor, name):
            descriptor.links_num += 1
            self.descriptor = descriptor
            self.name = name

        def show_info(self):
            print('%4d  %10s  %5d  %10d  %6d  %s' % (self.descriptor.NUM, self.descriptor.TYPE, self.descriptor.links_num, self.descriptor.length, len(self.descriptor.blocks), f'{self.name}->{self.descriptor.name}'))

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

    class Symlink:
        def __init__(self, name, descriptor, parent, content):
            self.name = name
            self.descriptor = descriptor
            self.parent = parent
            self.content = content

    class Directory:
        def __init__(self, name: str, descriptor, parent):
            self.name = name
            if parent is None:
                self.parent = self
            else:
                self.parent = parent
            self.descriptor = descriptor
            self.child_descriptors = []
            self.child_directories = []
            if parent is None:
                parentLink = DRIVER.Link(descriptor, '..')
            else:
                parentLink = DRIVER.Link(parent.descriptor, '..')
            self.child_descriptors.append(parentLink)
            self.child_descriptors.append(DRIVER.Link(descriptor, '.'))

    @staticmethod
    def open_path(pathname, isLastFile=False):
        if pathname == "":
            return DRIVER.cwd
        if pathname == '/':
            return DRIVER.FS.root
        pathArray = pathname.split('/')
        if pathname.startswith('/'):
            localCWD = DRIVER.FS.root
            pathArray.pop(0)
        else:
            localCWD = DRIVER.cwd
        new_localCWD = localCWD
        symlink_counter = 0
        if isLastFile:
            j = 0
            while j < len(pathArray):
                if symlink_counter > 20:
                    print('Too much symlink!')
                    return None
                pathPart = pathArray[j]
                if pathPart == '.':
                    j += 1
                    continue
                if pathPart == '..':
                    new_localCWD = localCWD.parent
                    localCWD = new_localCWD
                    j += 1
                    continue
                arrsize = len(pathArray)
                for i in range(len(localCWD.child_directories)):
                    if pathPart == localCWD.child_directories[i].name:
                        if localCWD.child_directories[i].descriptor.TYPE == 'symlink':
                            symlink_counter += 1
                            symPath = localCWD.child_directories[i].content
                            symPathArr = symPath.split('/')
                            if symPath.startswith('/'):
                                new_localCWD = DRIVER.FS.root
                                symPathArr.pop(0)
                            for ind, symm in enumerate(symPathArr):
                                pathArray.insert(j + ind + 1, symm)
                            break
                        elif j == len(pathArray) - 1 and localCWD.child_directories[i].descriptor.TYPE == 'regular':
                            return new_localCWD, localCWD.child_directories[i].descriptor
                        elif j == len(pathArray) - 1:
                            return None, None
                        else:
                            new_localCWD = localCWD.child_directories[i]
                            break
                if new_localCWD == localCWD and arrsize == len(pathArray):
                    return None, None
                localCWD = new_localCWD
                j += 1
            return new_localCWD
        else:
            j = 0
            while j < len(pathArray):
                if symlink_counter > 20:
                    print('Too much symlink!')
                    return None
                pathPart = pathArray[j]
                if pathPart == '.':
                    j += 1
                    continue
                if pathPart == '..':
                    new_localCWD = localCWD.parent
                    localCWD = new_localCWD
                    j += 1
                    continue
                arrsize = len(pathArray)
                for i in range(len(localCWD.child_directories)):
                    if pathPart == localCWD.child_directories[i].name:
                        if localCWD.child_directories[i].descriptor.TYPE == 'symlink':
                            symlink_counter += 1
                            symPath = localCWD.child_directories[i].content
                            symPathArr = symPath.split('/')
                            if symPath.startswith('/'):
                                new_localCWD = DRIVER.FS.root
                                symPathArr.pop(0)
                            for ind, symm in enumerate(symPathArr):
                                pathArray.insert(j+ind+1, symm)
                            break
                        else:
                            new_localCWD = localCWD.child_directories[i]
                            break
                if new_localCWD == localCWD and arrsize == len(pathArray):
                    return None
                localCWD = new_localCWD
                j += 1
            return new_localCWD


def mkfs(n):
    if DRIVER.FS is not None:
        print('Already initialised')
        return
    if not type(n) is int:
        print('n - int')
        return
    DRIVER.FS = DRIVER.File_system(n)
    print('Initialised')


def symlink(string, pathname):
    if DRIVER.FS is None:
        print('FS is not initialised')
        return
    if DRIVER.FS.descriptors_num >= DRIVER.FS.descriptors_max_num:
        print('All descriptors are in use')
        return
    oldPath = "/".join(pathname.split('/')[:-1])
    if len(pathname.split('/')) == 2 and oldPath == '':
        oldPath = '/'
    newSymName = pathname.split('/')[-1]
    if len(str(newSymName)) > DRIVER.MAX_FILE_NAME_LENGTH:
        print(f'File name is too large')
        return
    workingDir = DRIVER.open_path(oldPath)
    if workingDir is None:
        print(f"Incorrect path")
        return
    for directory in workingDir.child_directories:
        if newSymName == directory.name:
            print('Incorrect name')
            return
    descriptor_num = None
    for i, value in enumerate(DRIVER.FS.descriptorsBitmap):
        if not value:
            DRIVER.FS.descriptorsBitmap[i] = 1
            descriptor_num = i
            break
    newSymlinkDescriptor = DRIVER.Descriptor(descriptor_num, 'symlink', 0, newSymName, string)
    DRIVER.FS.descriptors.append(newSymlinkDescriptor)
    DRIVER.FS.descriptors_num += 1
    newSymlink = DRIVER.Symlink(newSymName, newSymlinkDescriptor, workingDir, string)
    workingDir.child_directories.append(newSymlink)
    workingDir.child_descriptors.append(newSymlinkDescriptor)
    print('Created')


def rmdir(pathname):
    if DRIVER.FS is None:
        print('FS is not initialised')
        return
    if pathname == '/':
        print('Can\'t delete root')
        return
    if pathname == '' or pathname == '.':
        print('Can\'t delete current')
        return
    if pathname == '..':
        print('Can\'t delete parent')
        return
    oldDir = DRIVER.open_path(pathname)
    if oldDir is None:
        print(f"Incorrect path")
        return
    if len(oldDir.child_descriptors) != 2:
        print('Can\'t delete nonempty dir')
        return
    if DRIVER.cwd == oldDir:
        print('Can\'t delete current')
    oldDir.parent.child_descriptors.remove(oldDir.descriptor)
    oldDir.parent.child_directories.remove(oldDir)
    oldDir.child_descriptors.clear()
    oldDir.child_directories.clear()
    oldDir.parent.descriptor.links_num -= 1
    DRIVER.FS.descriptors.remove(oldDir.descriptor)
    DRIVER.FS.descriptorsBitmap[oldDir.descriptor.NUM] = 0
    DRIVER.FS.descriptors_num -= 1
    del oldDir.descriptor
    del oldDir
    print('Deleted')


def cd(pathname):
    if DRIVER.FS is None:
        print('FS is not initialised')
        return
    if pathname == '/':
        DRIVER.cwd = DRIVER.FS.root
        return
    newDir = DRIVER.open_path(pathname)
    if newDir is None:
        print(f"Incorrect path")
        return
    DRIVER.cwd = newDir
    print('Changed')


def mkdir(pathname):
    if DRIVER.FS is None:
        print('FS is not initialised')
        return
    if DRIVER.FS.descriptors_num >= DRIVER.FS.descriptors_max_num:
        print('All descriptors are in use')
        return
    oldPath = "/".join(pathname.split('/')[:-1])
    if len(pathname.split('/')) == 2 and oldPath == '':
        oldPath = '/'
    newDirName = pathname.split('/')[-1]
    if len(str(newDirName)) > DRIVER.MAX_FILE_NAME_LENGTH:
        print(f'File name is too large')
    workingDir = DRIVER.open_path(oldPath)
    if workingDir is None:
        print(f"Incorrect path")
        return
    for directory in workingDir.child_directories:
        if newDirName == directory.name:
            print('Incorrect name')
            return
    descriptor_num = None
    for i, value in enumerate(DRIVER.FS.descriptorsBitmap):
        if not value:
            DRIVER.FS.descriptorsBitmap[i] = 1
            descriptor_num = i
            break
    newDirDescriptor = DRIVER.Descriptor(descriptor_num, 'directory', 0, newDirName)
    DRIVER.FS.descriptors.append(newDirDescriptor)
    DRIVER.FS.descriptors_num += 1
    newDir = DRIVER.Directory(newDirName, newDirDescriptor, workingDir)
    workingDir.child_descriptors.append(newDirDescriptor)
    workingDir.child_directories.append(newDir)
    print('Created')


def ls(pathname=''):
    if DRIVER.FS is None:
        print('FS is not initialised')
        return
    if pathname == '':
        print('   №        type  links      length  blocks  name')
        for descriptor in DRIVER.cwd.child_descriptors:
            descriptor.show_info()
        return
    workingDir = DRIVER.open_path(pathname)
    if workingDir is None:
        print(f"Incorrect path")
        return
    print('   №        type  links      length  blocks  name')
    for descriptor in workingDir.child_descriptors:
        descriptor.show_info()


def stat(name):
    if DRIVER.FS is None:
        print('FS is not initialised')
        return
    oldPath = "/".join(name.split('/')[:-1])
    if len(name.split('/')) == 2 and oldPath == '':
        oldPath = '/'
    descName = name.split('/')[-1]
    workingDir = DRIVER.open_path(oldPath)
    if workingDir is None:
        print(f"Incorrect path")
        return
    for descriptor in workingDir.child_descriptors:
        if descriptor.name == descName:
            print('   №        type  links      length  blocks  name')
            descriptor.show_info()
            return
    print(f'Incorrect name')


def create(name):
    if DRIVER.FS is None:
        print('FS is not initialised')
        return
    oldPath = "/".join(name.split('/')[:-1])
    if len(name.split('/')) == 2 and oldPath == '':
        oldPath = '/'
    descName = name.split('/')[-1]
    if len(str(descName)) > DRIVER.MAX_FILE_NAME_LENGTH:
        print(f'File name is too large')
    if DRIVER.FS.descriptors_num >= DRIVER.FS.descriptors_max_num:
        print('All descriptors are in use')
        return
    workingDir = DRIVER.open_path(oldPath)
    if workingDir is None:
        print(f"Incorrect path")
        return
    for descriptor in workingDir.child_descriptors:
        if descriptor.name == name:
            print('Incorrect name')
            return
    descriptor_num = None
    for i, value in enumerate(DRIVER.FS.descriptorsBitmap):
        if not value:
            DRIVER.FS.descriptorsBitmap[i] = 1
            descriptor_num = i
            break
    descriptor = DRIVER.Descriptor(descriptor_num, 'regular', 0, descName)
    DRIVER.FS.descriptors.append(descriptor)
    DRIVER.FS.descriptors_num += 1
    workingDir.child_descriptors.append(descriptor)
    print('   №        type  links      length  blocks  name')
    descriptor.show_info()


def open(name):
    if DRIVER.FS is None:
        print('FS is not initialised')
        return
    oldPath = "/".join(name.split('/')[:-1])
    if len(name.split('/')) == 2 and oldPath == '':
        oldPath = '/'
    descName = name.split('/')[-1]
    workingDir = DRIVER.open_path(oldPath)
    if workingDir is None:
        print(f"Incorrect path")
        return
    for descriptor in workingDir.child_descriptors:
        if descriptor.name == descName:
            if isinstance(descriptor, DRIVER.Descriptor) and descriptor.TYPE == 'symlink':
                print('Can\'t open symlink as file')
                return
            openedFile = DRIVER.Opened_file(descriptor)
            DRIVER.FS.opened_files.append(openedFile)
            print(f'Done. id = {openedFile.num_descriptor}!')
            return
    print(f'Incorrect name')


def truncate(name, size):
    if DRIVER.FS is None:
        print('FS is not initialised')
        return
    oldPath = "/".join(name.split('/')[:-1])
    if len(name.split('/')) == 2 and oldPath == '':
        oldPath = '/'
    descName = name.split('/')[-1]
    workingDir = DRIVER.open_path(oldPath)
    if workingDir is None:
        print(f"Incorrect path")
        return
    for descriptor in workingDir.child_descriptors:
        if descriptor.name == descName and descriptor.TYPE == 'regular':
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


def link(name1, name2):
    if DRIVER.FS is None:
        print('FS is not initialised')
        return
    filePath = "/".join(name1.split('/')[:-1])
    if len(name1.split('/')) == 2 and filePath == '':
        filePath = '/'
    descFileName = name1.split('/')[-1]
    workingFileDir = DRIVER.open_path(filePath)
    if workingFileDir is None:
        print(f"Incorrect path")
        return
    linkPath = "/".join(name2.split('/')[:-1])
    if len(name2.split('/')) == 2 and linkPath == '':
        linkPath = '/'
    descLinkName = name2.split('/')[-1]
    workingLinkDir = DRIVER.open_path(linkPath)
    if workingLinkDir is None:
        print(f"Incorrect path")
        return
    if len(str(descLinkName)) > DRIVER.MAX_FILE_NAME_LENGTH:
        print(f'File name is too large')
    for descriptor in workingLinkDir.child_descriptors:
        if descriptor.name == descLinkName:
            print(f'Incorrect name2')
            return
    for descriptor in workingFileDir.child_descriptors:
        if descriptor.name == descFileName:
            if isinstance(descriptor, DRIVER.Descriptor) and descriptor.TYPE == 'symlink':
                print('Can\'t do link to symlink file')
                return
            if isinstance(descriptor, DRIVER.Link):
                print('Can\'t create link to link')
                return
            new_link = DRIVER.Link(descriptor, descLinkName)
            descriptor.links.append(new_link)
            workingLinkDir.child_descriptors.append(new_link)
            print('   №        type  links      length  blocks  name')
            new_link.show_info()
            return
    print(f'Incorrect name1')


def unlink(name):
    if DRIVER.FS is None:
        print('FS is not initialised')
        return
    oldPath = "/".join(name.split('/')[:-1])
    if len(name.split('/')) == 2 and oldPath == '':
        oldPath = '/'
    descName = name.split('/')[-1]
    workingDir = DRIVER.open_path(oldPath)
    if workingDir is None:
        print(f"Incorrect path")
        return
    for descriptor in workingDir.child_descriptors:
        if descriptor.name == descName:
            if isinstance(descriptor, DRIVER.Descriptor):
                if descriptor.TYPE == 'directory':
                    print('Can\'t unlink directory')
                    return
                workingDir.child_descriptors.remove(descriptor)
                descriptor.links_num -= 1
                if descriptor.links_num == 0:
                    DRIVER.FS.descriptorsBitmap[descriptor.NUM] = 0
                    del descriptor
                print('Link deleted')
            else:
                descriptor.descriptor.links_num -= 1
                descriptor.descriptor.links.remove(descriptor)
                workingDir.child_descriptors.remove(descriptor)
                if descriptor.descriptor.links_num == 0:
                    DRIVER.FS.descriptorsBitmap[descriptor.descriptor.NUM] = 0
                    del descriptor.descriptor
                print('Link deleted')
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
    print(f'Incorrect ID')


def seek(fd, offset):
    if DRIVER.FS is None:
        print('FS is not initialised')
        return
    if fd not in DRIVER.FS.opened_files_num_descriptors:
        print(f'Incorrect ID')
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
        print('Val == 1 byte')
        return
    if fd not in DRIVER.FS.opened_files_num_descriptors:
        print(f'Incorrect ID')
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
        print(f'Incorrect ID')
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


if __name__ == '__main__':
    while True:
        try:
            ans = input('~ ')
            ans = ans.split(' ')
            eval(f'{ans[0]}({",".join(ans[1:])})')
        except:
            print('Error!')
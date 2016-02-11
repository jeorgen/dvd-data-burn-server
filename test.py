#!/usr/bin/env python

import unittest
import os
import tempfile
import shutil
from  utils import ModuleAttributesContextManager, unique_in_time
import session_server as ts
import burn_server as bs

def create_tree(base_dir, structure):
    paths_created = []
    for path in structure:
        long_path = os.path.join(base_dir, path)
        paths_created.append(long_path)
        ts.make_file_path(long_path)
        with open(long_path, 'w') as fo:
            fo.write('foo')
    return paths_created

class TestBurnServer(unittest.TestCase):

    def setUp(self):
        bs.WATCHED_FOLDER = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(bs.WATCHED_FOLDER)

    def test_get_top_level_files(self):
        """Check that the number of top level files are correct"""
        base_dir = tempfile.mkdtemp()
        test_files = ['foo','bar','baz']
        create_tree(base_dir, test_files)
        files = bs.get_top_level_files(base_dir)
        self.assertEqual(len(files), len(test_files))
        shutil.rmtree(base_dir)

    def test_get_directories(self):
        """Check that the number of top level directories are correct"""
        test_paths = ['foo/bar','bar/bar','baz/bar']
        create_tree(bs.WATCHED_FOLDER, test_paths)
        paths = bs.get_directories(bs.WATCHED_FOLDER)
        self.assertEqual(len(paths), len(test_paths))

    def test_dir_ready(self):
        """Check if there is a burn file"""
        create_tree(bs.WATCHED_FOLDER, ['data_dir/data','burn_file'])
        self.assertTrue(bs.dir_ready(bs.WATCHED_FOLDER))

    def test_dir_not_ready(self):
        """Check that there is not a burn file"""
        create_tree(bs.WATCHED_FOLDER, ['data_dir/data',])
        self.assertFalse(bs.dir_ready(bs.WATCHED_FOLDER))

    def test_get_burn_candidates(self):
        """Check and see how many burn candidate there are"""
        create_tree(bs.WATCHED_FOLDER, ['session1/data/foo', 'session1/burn_signal]', 'session2/data/foo'])
        self.assertTrue(len(bs.get_burn_candidates())== 1)

    def test_burn(self):
        """ Check if 'xorriso' is in the resulting command"""
        res = bs.burn(bs.WATCHED_FOLDER, testing = True)
        self.assertTrue('xorriso' in res[0])

    def test_get_sub_directory(self):
        create_tree(bs.WATCHED_FOLDER, ['foo/bar',])
        assert (bs.get_sub_directory(bs.WATCHED_FOLDER).endswith ('/foo'))

class TestSessionServer(unittest.TestCase):

    def setUp(self):
        ts.SRC_DIR = tempfile.mkdtemp()
        ts.SESSION_BASE_PARENT_DIR = tempfile.mkdtemp()
        ts.MINUTES_BETWEEN_SESSIONS = 1
        ts.POLLING_INTERVAL_IN_SECS = 5
        ts.FILE_COUNT_FOR_IMMEDIATE_SESSION = 2
        ts.reconfigure_commands()

    def tearDown(self):
        shutil.rmtree(ts.SRC_DIR )
        shutil.rmtree(ts.SESSION_BASE_PARENT_DIR)

    def test_enough(self):
        with ModuleAttributesContextManager(module = ts, values = {'FILE_COUNT_FOR_IMMEDIATE_SESSION':3}):
            files = (1,2,3)
            self.assertTrue(ts.enough(files))

            files = (1,2,3,4)
            self.assertTrue(ts.enough(files))

            files = (1,2)
            self.assertFalse(ts.enough(files))

            files = ()
            self.assertFalse(ts.enough(files))

    def test_compute_now_in_minutes(self):
        self.assertEqual(type(ts.compute_now_in_minutes()), type(4))

    def test_minutes_since_last_session(self):
        self.assertEqual(type(ts.minutes_since_last_session()), type(4))

    def test_time_to_session(self):
        with ModuleAttributesContextManager(module = ts, values = {'MINUTES_BETWEEN_SESSIONS':12}):
            self.assertFalse(ts.time_to_session(10))
            self.assertTrue(ts.time_to_session(20))

    def test_add_burn_signal(self):
        path = os.path.join(ts.SESSION_BASE_PARENT_DIR, "testburn")
        ts.add_burn_signal(path)
        self.assertTrue(os.path.exists(os.path.join(path, 'burn_signal')))

    def test_get_new_files(self):
        structure = [ 'foo/bar/baz.txt', 'foo/bar/baz2.txt','foo/blurt.txt', 'foo/bletch/flum.txt']
        create_tree(ts.SRC_DIR, structure)
        files_list = ts.get_new_files(ts.FIND_ALL_COMMAND)
        self.assertTrue(len(files_list) == len(structure))

    def test_copy_file(self):
        path = 'foo/bar/baz.txt'
        paths_created = create_tree(ts.SRC_DIR, [path])
        src = paths_created[0]
        dst = os.path.join(ts.SRC_DIR, "foo", path)
        ts.copy_file(src, dst)
        self.assertTrue(os.path.exists(dst))


    def test_copy_files(self):
        paths = ['foo/bar/baz.txt', 'foo/bletch.txt']
        paths_created = create_tree(ts.SRC_DIR, paths)
        dst_base_dir = os.path.join(ts.SESSION_BASE_PARENT_DIR, 'foo')
        ts.copy_files(paths_created, dst_base_dir)
        for path in paths:
            dst = os.path.join(dst_base_dir, path)
            self.assertTrue(os.path.exists(dst))

    def test_new_signal_dir(self):
        signal_dir = ts.new_signal_dir()
        dir_path, signal = os.path.split(signal_dir)
        self.assertFalse(not signal)
        self.assertEqual(dir_path, ts.SESSION_BASE_PARENT_DIR) 

    def test_session(self):
        structure = [ 'foo/bar/baz.txt', 'foo/bar/baz2.txt','foo/blurt.txt', 'foo/bletch/flum.txt']
        files = create_tree(ts.SRC_DIR, structure)
        signal_dir = ts.session(files)
        files_dir = os.path.join(ts.SESSION_BASE_PARENT_DIR, signal_dir, 'files')
        for path in structure:
            dst = os.path.join(files_dir, path)
            self.assertTrue(os.path.exists(dst))



    # def test_do_job():
    #     structure = [ 'foo/bar/baz.txt', 'foo/bar/baz2.txt','foo/blurt.txt', 'foo/bletch/flum.txt']
    #     files = create_tree(ts.SRC_DIR, structure)        
    #     do_job()
    #     if last_session_time == 0:
    #         files_to_session = get_new_files(FIND_ALL_COMMAND)
    #     else:
    #         minutes_since_last = minutes_since_last_session()
    #         files_to_session = get_new_files(FIND_COMMAND + [minutes_since_last +1]) # +1 min. extra for safety
    #         if not enough(files_to_session) and not time_to_session(minutes_since_last):
    #             files_to_session = None
    #     session(files_to_session)

if __name__ == '__main__':
    unittest.main()

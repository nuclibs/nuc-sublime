import sys, os, subprocess, shutil, shlex, json, codecs, time
import sublime, sublime_plugin
import Default

class NucProject(sublime_plugin.EventListener):
    def __init__(self):
        global _nuc_
        _nuc_ = self
        self.target = "html5"
        self.build_run = False
        self.build_debug = False
        self.build_compile = False
        self.build_onlydata = False
        self.build_noshaders = False
        self.build_nohaxe = False
        self.build_watch = False
        self.build_type = "build"
        self.nuc_file = ""
        self.nuc_file_type = ""
        # self.hxml_file = ""
        self.on_finished = None
        # print("[nuc] __init__")

    def refresh_info(self, build):
        if self.nuc_file_type == "nuc":
            self.set_hxml_autocomplete(build)
        elif self.nuc_file_type == "hxml":
            self.set_hxml_file(self.nuc_file)
        else:
            pass

    def set_nuc_file(self, file_name):
        if not file_name:
            print("[nuc] can't set nuc file" + str(file_name))
            return

        file_name = str(file_name)
        # print("[nuc] set nuc file to " + file_name)
        sublime.status_message("set nuc file to " + file_name)

        self.nuc_file = file_name

        fn, ext = os.path.splitext(self.nuc_file)

        if "nuc" in ext:
            self.nuc_file_type = "nuc"
        elif "hxml" in ext:
            self.nuc_file_type = "hxml"

        self.refresh_info(True)

    def set_hxml_file(self, file_name):
        from haxe_sublime.haxe import _haxe_
        _haxe_.set_hxml_file(file_name)

    def set_hxml_autocomplete(self, build):
        working_dir = _nuc_.get_working_dir()
        hxml_path = working_dir + '/build/project-' + self.target + '.hxml'
        if os.path.isfile(hxml_path):
            # print ("[nuc] found hxml file, set autocompletion for " + hxml_path)
            self.set_hxml_file(hxml_path)
        else:
            if build:
                sublime.status_message("build hxml, cause file is not found in: " + hxml_path)

                self.on_finished = "nuc_set_autocompletion"
                build_noshaders = self.build_noshaders
                build_nohaxe = self.build_nohaxe
                self.build_noshaders = True
                self.build_nohaxe = True
                sublime.active_window().run_command("nuc_build", "silent")
                self.build_noshaders = build_noshaders
                self.build_nohaxe = build_nohaxe
            else:
                sublime.status_message("can't set hxml for autocompletion, file is not found in: " + hxml_path)


    def set_nuc_target_by_index( self, index ):
        _targets = self.get_targets()
        _target = _targets[index]
        self.target = _target[0].lower()
        print("[nuc] set build target to " + self.target)

        self.refresh_info(True)
        # if self.target == "html5":
            # os.system("haxelib run nuc server")
        # self.refresh_info()

    def get_targets(self):

        result = []

        if not self.nuc_file:
            sublime.status_message("nuc file is not set")
            return result

        result.append(['html5'])
        result.append(['windows'])
        result.append(['android-native'])
        result.append(['linux'])
        result.append(['osx'])
        result.append(['ios'])

        # if self.info_json:
        #     _invalid = self.info_json['targets_invalid']
        #     result[:] = [_item for _item in result if not _item[0].lower() in _invalid ]
        #     result.insert(0, ['unavailable from ' + self.system, ", ".join(_invalid) ])

        # else :
        #     result.append(['Error', 'Failed to retrieve nuc info from project. View -> Show Console for more info to report!'])

        return result

    def get_build_settings(self):
        result = []

        if self.nuc_file:
            result.append(['Nuc file', self.nuc_file])
        else:
            result.append(['No Nuc file', 'specify a Nuc file first'])
            return result

        if self.nuc_file_type is not "nuc":
            return result

        if self.target:
            result.append(['Target', self.target])
        else:
            result.append(['Target', "hxml file"])

        result.append(['Debug build', "currently : " + str(self.build_debug).lower() ])
        result.append(['Watch build', "currently : " + str(self.build_watch).lower() ])
        result.append(['Build type', "currently : " + str(self.build_type).lower() ])
        # result.append(['Package output folder', "generates a zip to output folder"])
        # result.append(['Clean output folder', "delete the output folder"])
        # result.append(['Clean build output', "delete the build folder"])

        return result

    def get_working_dir(self):
        cwd = os.path.dirname(self.nuc_file)
        cwd = os.path.normpath( cwd )

        return cwd

def panel(_window, options, done, flags=0, sel_index=0, on_highlighted=None):
    sublime.set_timeout(lambda: _window.show_quick_panel(options, done, flags, sel_index, on_highlighted), 10)

class NucSetProjectContextCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        from .nuc import _nuc_
        _nuc_.set_nuc_file(self.view.file_name())
        print("[nuc] set project file")

    def is_visible(self):
        pt = self.view.sel()[0].b
        scope = self.view.scope_name(pt)
        if ("source.nuc" in scope) or ("source.hxml" in scope):
            return True
        else:
            return False

class NucSetProjectCommand(sublime_plugin.WindowCommand):

    def run(self):
        from .nuc import _nuc_

        # view = self.window.active_view()
        _nuc_.set_nuc_file(self.view.file_name())
        print("[nuc] run nuc set project file")

    def is_visible(self):
        view = self.window.active_view()
        pt = view.sel()[0].b
        scope = view.scope_name(pt)

        if ("source.nuc" in scope) or ("source.hxml" in scope):
            return True
        else:
            return False

class NucSetAutocompletionCommand(sublime_plugin.WindowCommand):

    def run(self):
        from .nuc import _nuc_
        print("[nuc] nuc set autocompletion file")
        _nuc_.refresh_info(False)

class NucSetBuildSettingsCommand(sublime_plugin.WindowCommand):

    def run(self, sel_index=0):
        from .nuc import _nuc_, panel

        view = self.window.active_view()
        panel(self.window, _nuc_.get_build_settings(), self.on_select, sel_index=sel_index)

    def on_select(self, index):
        from .nuc import _nuc_

            #the nuc file
        if index == 0:
            if _nuc_.nuc_file:
                self.window.open_file(_nuc_.nuc_file)

            #target
        if index == 1:
            self.window.run_command('nuc_set_build_target')

            #debug flag
        if index == 2:
            if _nuc_.build_debug:
                _nuc_.build_debug = False
            else:
                _nuc_.build_debug = True

            print("[nuc] toggle build debug, now at " + str(_nuc_.build_debug))
            self.run(sel_index=2)

            #verbose flag
        if index == 3:
            if _nuc_.build_watch:
                _nuc_.build_watch = False
            else:
                _nuc_.build_watch = True

            print("[nuc] toggle build watch, now at " + str(_nuc_.build_watch))

            self.run(sel_index=3)

            #build type flag
        if index == 4:
            if _nuc_.build_type == 'run':
                _nuc_.build_type = 'build'
            elif _nuc_.build_type == 'build':
                _nuc_.build_type = 'compile'
            elif _nuc_.build_type == 'compile':
                _nuc_.build_type = 'launch'
            elif _nuc_.build_type == 'launch':
                _nuc_.build_type = 'run'

            # print("[nuc] switched build type, now at " + str(_nuc_.build_type))

            self.run(sel_index=4)

    def is_visible(self):
        view = self.window.active_view()
        pt = view.sel()[0].b
        scope = view.scope_name(pt)

        if ("source.nuc" in scope) or ("source.hxml" in scope):
            return True
        else:
            return False

class NucServerCommand(sublime_plugin.WindowCommand):

    def run(self):
        os.system("haxelib run nuc server")


class NucSetBuildTargetCommand(sublime_plugin.WindowCommand):

    def run(self):
        from .nuc import _nuc_, panel

        # view = self.window.active_view()
        panel(self.window, _nuc_.get_targets(), self.on_target_select, 0, 0)

    def on_target_select(self, index):
        from .nuc import _nuc_

        if index > 0:
            _nuc_.set_nuc_target_by_index(index)

    # def is_visible(self):
    #     from ..nuc import _nuc_

    #     view = self.window.active_view()
    #     pt = view.sel()[0].b
    #     scope = view.scope_name(pt)
    #     if ("source.nuc" in scope):
    #         if _nuc_.nuc_file:
    #             return True

    #     return False


class NucBuild(Default.exec.ExecCommand):

    def run(self, cmd = None, shell_cmd = None, file_regex = "", line_regex = "", working_dir = "",
            encoding = "utf-8", env = {}, quiet = False, kill = False,
            word_wrap = True, syntax = "Packages/Text/Plain text.tmLanguage",
            # Catches "path" and "shell"
            **kwargs):

        try:
            if self.proc:
                super(NucBuild, self).run(kill=True)
        except Exception as e:
            print("[nuc] couldn't kill previous executable: probably it ended > " + str(e))

        self.proc = None

        if kill:
            return

        from .nuc import _nuc_

        print(cmd)

        if not _nuc_.nuc_file and _nuc_.nuc_file == "":
            sublime.status_message("can't build, nuc file is not set")
            return

        working_dir = _nuc_.get_working_dir()

        cmd = []
        if _nuc_.nuc_file_type == "nuc":
            cmd = self.get_nuc_cmd(_nuc_)
        elif _nuc_.nuc_file_type == "hxml":
            cmd = self.get_hxml_cmd(_nuc_)
        else:
            pass
        print(_nuc_.nuc_file_type)

        print("[nuc] build: " + " ".join(cmd))

        super(NucBuild, self).run( 
                cmd= None, 
                shell_cmd= " ".join(cmd),
                file_regex= file_regex, 
                line_regex= line_regex, 
                working_dir= working_dir, 
                encoding= encoding, 
                env= env, 
                quiet= False, 
                kill= kill, 
                word_wrap= word_wrap, 
                syntax= syntax, 
                **kwargs)

    def get_nuc_cmd(self, _nuc_):
        cmd = [
            "haxelib", "run", "nuc", 
        ]

        if _nuc_.build_type == "launch":
            cmd.append("launch")
            cmd.append(_nuc_.target)
        else:
            if _nuc_.build_type == "run":
                cmd.append("run")
            else:
                cmd.append("build")

            cmd.append(_nuc_.target)

            if _nuc_.build_type == "compile":
                cmd.append("--compile")

            if _nuc_.build_debug:
                cmd.append("--debug")

            if _nuc_.build_onlydata:
                cmd.append("--onlydata")

            if _nuc_.build_noshaders:
                cmd.append("--noshaders")

            if _nuc_.build_nohaxe:
                cmd.append("--nohaxe")

            if _nuc_.build_watch:
                cmd.append("--watch")

        return cmd

    def get_hxml_cmd(self, _nuc_):
        cmd = [
            "haxe", _nuc_.nuc_file
        ]
        return cmd

    def on_finished(self, proc):
        super().on_finished(proc)
        if _nuc_.on_finished:
            self.window.run_command(_nuc_.on_finished)
            _nuc_.on_finished = None
            self.window.run_command("hide_panel")

print("[nuc] loaded nuc file")

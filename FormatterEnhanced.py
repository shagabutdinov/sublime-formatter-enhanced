import sublime
import sublime_plugin
import re
import subprocess
import os
import difflib

def show_output(text):
  panel = sublime.active_window().create_output_panel('formatter_enhanced')
  panel.run_command('insert_text', {'point': 0, 'text': text})

  sublime.active_window().run_command('show_panel', {
    'panel': 'output.formatter_enhanced',
  })

class FormatterEnhanced(sublime_plugin.EventListener):
    def on_post_save_async(self, view):
        if view.size() > 1024 * 32:
            return

        content = view.substr(sublime.Region(0, view.size()))
        result = content
        scope = view.scope_name(0)
        executed = False

        for formatter in view.settings().get('formatter_enhanced', []):
            if not re.match(formatter['scope'], scope):
                continue

            try:
                process = subprocess.Popen(
                    formatter['command'],
                    stdout=subprocess.PIPE,
                    stdin=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    shell=True,
                    cwd=os.path.dirname(view.file_name()),
                )

                process.stdin.write(str.encode(result))
                process.stdin.close()

                result = process.stdout.read().decode('utf-8')
                status = process.wait()
                if status != 0:
                    raise Exception(
                        'Process exited with wrong exit ' +
                            'code {0}'.format(status),
                    )


                executed = True
            except Exception as error:
                error_output = process.stderr.read().decode('utf-8')

                if error_output != None and error_output != '':
                    show_output(error_output)

                return

        if not executed:
            return

        if view.substr(sublime.Region(0, view.size())) != content:
            return

        changes = difflib.SequenceMatcher(None, content, result).get_opcodes()

        view.run_command('formatter_enhanced_replace', {
            'changes': changes,
            'content': result,
        })

class FormatterEnhancedReplace(sublime_plugin.TextCommand):
    def run(self, edit, changes = [], content = None):
        changes.reverse()

        for change in changes:
            if change[0] == 'replace':
                self.view.replace(
                    edit,
                    sublime.Region(change[1], change[2]),
                    content[change[3]:change[4]],
                )
            elif change[0] == 'delete':
                self.view.erase(edit, sublime.Region(change[1], change[2]))
            elif change[0] == 'insert':
                self.view.insert(edit, change[1], content[change[3]:change[4]])
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# This file is part of tasker
#
# Copyright (c) 2020 Lorenzo Carbonell Cerezo <a.k.a. atareao>
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

import gi
try:
    gi.require_version('Gtk', '3.0')
    gi.require_version('Gio', '2.0')
except ValueError as e:
    print(e)
    exit(1)
from gi.repository import Gtk
from gi.repository import Gio
from pathlib import Path
import os
import config
import shutil
from config import _
from configurator import Configuration
from basedialog import BaseDialog
from add_project import AddProjectDialog
from add_context import AddContextDialog
from add_tag import AddTagDialog
from list_box_string import ListBoxString
from list_box_string_type import ListBoxStringType

def select_value_in_combo(combo, value):
    model = combo.get_model()
    for i, item in enumerate(model):
        if value == item[1]:
            combo.set_active(i)
            return
    combo.set_active(0)


def get_selected_value_in_combo(combo):
    model = combo.get_model()
    return model.get_value(combo.get_active_iter(), 1)


class Preferences(BaseDialog):
    def __init__(self):
        BaseDialog.__init__(self, _('Preferences'), None, ok_button=True,
                            cancel_button=True)
        self.load()

    def init_ui(self):
        BaseDialog.init_ui(self)

        self.notebook = Gtk.Notebook.new()
        self.grid.attach(self.notebook, 0, 0, 1, 1)

        self._build_page_general()
        self._build_page_projects()
        self._build_page_contexts()
        self._build_tags()
        self._build_behaviors()

    def _build_behaviors(self, ):
        page05 = self._new_page('Behaviors')
        label = Gtk.Label.new(_('Filter by projects'))
        label.set_property('halign', Gtk.Align.START)
        page05.attach(label, 0, 0, 1, 1)
        self.filter_projects = Gtk.Switch.new()
        self.filter_projects.set_property('halign', Gtk.Align.CENTER)
        page05.attach(self.filter_projects, 1, 0, 1, 1)

    def _build_tags(self):
        page04 = self._new_page('Tags')
        self.tags = ListBoxStringType()
        self.tags.set_size_request(250, 250)
        page04.attach(self.tags, 0, 0, 3, 3)
        box = Gtk.Box.new(Gtk.Orientation.VERTICAL, 5)
        page04.attach(box, 3, 0, 1, 2)
        button_add_tag = Gtk.Button.new_with_label(_('Add tag'))
        button_add_tag.connect('clicked', self.on_button_add_tag_clicked)
        box.add(button_add_tag)
        button_remove_tag = Gtk.Button.new_with_label(_('Remove tag'))
        button_remove_tag.connect('clicked', self.on_button_remove_tag_clicked)
        box.add(button_remove_tag)

    def _build_page_contexts(self):
        page03 = self._new_page('Contexts')
        self.contexts = ListBoxString()
        self.contexts.set_size_request(250, 250)
        page03.attach(self.contexts, 0, 0, 3, 3)
        box = Gtk.Box.new(Gtk.Orientation.VERTICAL, 5)
        page03.attach(box, 3, 0, 1, 2)
        button_add_context = Gtk.Button.new_with_label(_('Add context'))
        button_add_context.connect('clicked', self.on_button_add_context_clicked)
        box.add(button_add_context)
        button_remove_context = Gtk.Button.new_with_label(_('Remove context'))
        button_remove_context.connect('clicked', self.on_button_remove_context_clicked)
        box.add(button_remove_context)

    def _build_page_projects(self):
        page02 = self._new_page('Projects')
        self.projects = ListBoxString()
        self.projects.set_size_request(250, 250)
        page02.attach(self.projects, 0, 0, 3, 3)
        box = Gtk.Box.new(Gtk.Orientation.VERTICAL, 5)
        page02.attach(box, 3, 0, 1, 2)
        button_add_project = Gtk.Button.new_with_label(_('Add project'))
        button_add_project.connect('clicked', self.on_button_add_project_clicked)
        box.add(button_add_project)
        button_remove_project = Gtk.Button.new_with_label(_('Remove project'))
        button_remove_project.connect('clicked', self.on_button_remove_projet_clicked)
        box.add(button_remove_project)

    def _build_page_general(self):
        page01 = self._new_page('General')
        label = Gtk.Label.new(_('Theme light:'))
        label.set_property('halign', Gtk.Align.START)
        page01.attach(label, 0, 0, 1, 1)
        self.theme_light = Gtk.Switch.new()
        self.theme_light.set_property('halign', Gtk.Align.CENTER)
        page01.attach(self.theme_light, 1, 0, 1, 1)
        label = Gtk.Label.new(_('Autostart'))
        label.set_property('halign', Gtk.Align.START)
        page01.attach(label, 0, 1, 1, 1)
        self.autostart = Gtk.Switch.new()
        self.autostart.set_property('halign', Gtk.Align.CENTER)
        page01.attach(self.autostart, 1, 1, 1, 1)
        page01.attach(Gtk.Separator(), 0, 2, 2, 1)
        label = Gtk.Label.new(_('Number of tasks in menu:'))
        label.set_property('halign', Gtk.Align.START)
        page01.attach(label, 0, 3, 1, 1)
        self.todos = Gtk.SpinButton.new_with_range(1, 20, 1)
        page01.attach(self.todos, 1, 3, 1, 1)
        page01.attach(Gtk.Separator(), 0, 4, 2, 1)
        label = Gtk.Label.new(_('Todo file:'))
        label.set_property('halign', Gtk.Align.START)
        page01.attach(label, 0, 5, 1, 1)
        todofilter = Gtk.FileFilter.new()
        todofilter.add_pattern('*.txt')
        todofilter.add_mime_type('text/plain')
        self.todo_file = Gtk.FileChooserButton.new(_('Todo file'), Gtk.FileChooserAction.OPEN)
        self.todo_file.add_filter(todofilter)
        page01.attach(self.todo_file, 1, 5, 1, 1)

    def _new_page(self, label):
        newPage = Gtk.Grid.new()
        newPage.set_row_spacing(10)
        newPage.set_column_spacing(10)
        newPage.set_margin_bottom(10)
        newPage.set_margin_start(10)
        newPage.set_margin_end(10)
        newPage.set_margin_top(10)
        self.notebook.append_page(newPage, Gtk.Label.new(_(label)))
        return newPage

    def load(self):
        configuration = Configuration()
        preferences = configuration.get('preferences')
        self.theme_light.set_active(preferences.get('theme-light'))
        autostart_file = 'todotxt-indicator-autostart.desktop'
        if os.path.exists(os.path.join(
                os.getenv('HOME'), '.config/autostart', autostart_file)):
            self.autostart.set_active(True)
        else:
            self.autostart.set_active(False)
        self.todos.set_value(preferences['todos'])

        self.projects.add_all(preferences['projects'])
        self.contexts.add_all(preferences['contexts'])
        self.tags.add_all(preferences['tags'])
        
        todo_file = Path(os.path.expanduser(preferences['todo-file']))
        if not todo_file.exists():
            if not todo_file.parent.exists():
                os.makedirs(todo_file.parent)
            todo_file.touch()
        self.todo_file.set_file(Gio.File.new_for_path(todo_file.as_posix()))
        self.filter_projects.set_active(preferences.get('filter-projects'))

    def save(self):
        configuration = Configuration()
        preferences = configuration.get('preferences')
        preferences['theme-light'] = self.theme_light.get_active()
        preferences['todos'] = int(self.todos.get_value())
        preferences['todo-file'] = self.todo_file.get_file().get_path()
        preferences['projects'] = self.projects.get_items()
        preferences['contexts'] = self.contexts.get_items()
        preferences['tags'] = self.tags.get_items()
        preferences['filter-projects'] = self.filter_projects.get_active()
        configuration.set('preferences', preferences)
        configuration.save()
        autostart_file = 'todotxt-indicator-autostart.desktop'
        autostart_file = os.path.join(
                os.getenv('HOME'), '.config/autostart', autostart_file)
        if self.autostart.get_active():
            if not os.path.exists(os.path.dirname(autostart_file)):
                os.makedirs(os.path.dirname(autostart_file))
            shutil.copyfile(config.AUTOSTART, autostart_file)
        else:
            if os.path.exists(autostart_file):
                os.remove(autostart_file)

    def on_button_add_project_clicked(self, widget):
        addProjectDialog = AddProjectDialog()
        if addProjectDialog.run() == Gtk.ResponseType.ACCEPT:
            project_name = addProjectDialog.get_name()
            self.projects.add_item(project_name)
            self.projects.show()
        addProjectDialog.destroy()

    def on_button_remove_projet_clicked(self, widget):
        selected_row = self.projects.get_selected_row()
        if selected_row:
            self.projects.remove_item(selected_row.get_name())

    def on_button_add_context_clicked(self, widget):
        addContextDialog = AddContextDialog()
        if addContextDialog.run() == Gtk.ResponseType.ACCEPT:
            context_name = addContextDialog.get_name()
            self.contexts.add_item(context_name)
            self.contexts.show()
        addContextDialog.destroy()
    
    def on_button_remove_context_clicked(self, widget):
        selected_row = self.contexts.get_selected_row()
        if selected_row:
            self.contexts.remove_item(selected_row.get_name())
            self.contexts.show_all()

    def on_button_add_tag_clicked(self, widget):
        addTagDialog = AddTagDialog()
        if addTagDialog.run() == Gtk.ResponseType.ACCEPT:
            tag_name = addTagDialog.get_name()
            tag_type = addTagDialog.get_type()
            self.tags.add_item({'name': tag_name, 'type': tag_type})
            self.tags.show()
        addTagDialog.destroy()

    def on_button_remove_tag_clicked(self, widget):
        selected_row = self.tags.get_selected_row()
        if selected_row:
            self.tags.remove_item(selected_row.get_name())
            self.tags.show_all()

if __name__ == '__main__':
    preferences = Preferences()
    response = preferences.run()
    if response == Gtk.ResponseType.ACCEPT:
        preferences.save()
    preferences.destroy()

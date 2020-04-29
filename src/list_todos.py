#!/usr/bin/env python
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
except Exception as e:
    print(e)
    exit(-1)
from gi.repository import Gtk
import os
from pathlib import Path
import todotxtio
from basedialog import BaseDialog
from list_box_check import ListBoxCheck
from list_box_todo import ListBoxTodo
from add_todo import AddTodoDialog
from config import _
from configurator import Configuration


def select_value_in_combo(combo, value):
    model = combo.get_model()
    for i, item in enumerate(model):
        if value == item[1]:
            combo.set_active(i)
            return
    combo.set_active(0)


def get_selected_value_in_combo(combo):
    aniter = combo.get_active_iter()
    if aniter:
        model = combo.get_model()
        return model.get_value(combo.get_active_iter(), 1)


class ListTodos(BaseDialog):
    """docstring for ListTodos"""
    def __init__(self):
        BaseDialog.__init__(self, _('List of tasks'), None, ok_button=True,
                            cancel_button=True)
        self.load()

    def init_ui(self):
        BaseDialog.init_ui(self)

        self.todos = ListBoxTodo()
        self.todos.set_size_request(300, 500)
        self.grid.attach(self.todos, 0, 0, 1, 1)

        expander = Gtk.Expander.new(_('Filter tasks'))

        expander_grid = Gtk.Grid.new()
        expander_grid.set_row_spacing(10)
        expander_grid.set_margin_bottom(10)
        expander_grid.set_margin_start(10)
        expander_grid.set_margin_end(10)
        expander_grid.set_margin_top(10)

        expander.add(expander_grid)
        self.grid.attach(expander, 0, 1, 1, 1)

        label = Gtk.Label.new(_('Priority:'))
        label.set_halign(Gtk.Align.START)
        label.set_valign(Gtk.Align.CENTER)
        label.set_margin_end(10)
        expander_grid.attach(label, 0, 0, 1, 1)

        priority_store = Gtk.ListStore(str, int)
        priority_store.append(['-', -1])
        for i in range(0, 26):
            priority_store.append([chr(i + 65), i])
        self.priority = Gtk.ComboBox.new()
        self.priority.connect('changed', self.on_priority_project_context_changed)
        self.priority.set_model(priority_store)
        cell1 = Gtk.CellRendererText()
        self.priority.pack_start(cell1, True)
        self.priority.add_attribute(cell1, 'text', 0)
        expander_grid.attach(self.priority, 1, 0, 1, 1)

        self.project = None
        self.context = None
        self.tags = []

        label = Gtk.Label.new(_('Select project:'))
        label.set_halign(Gtk.Align.START)
        label.set_valign(Gtk.Align.CENTER)
        label.set_margin_end(10)
        expander_grid.attach(label, 0, 1, 1, 1)

        project_store = Gtk.ListStore(str, str)
        self.project = Gtk.ComboBox.new()
        self.project.connect('changed', self.on_priority_project_context_changed)
        self.project.set_model(project_store)
        cell1 = Gtk.CellRendererText()
        self.project.pack_start(cell1, True)
        self.project.add_attribute(cell1, 'text', 0)
        expander_grid.attach(self.project, 1, 1, 1, 1)

        label = Gtk.Label.new(_('Select context:'))
        label.set_halign(Gtk.Align.START)
        label.set_valign(Gtk.Align.CENTER)
        label.set_margin_end(10)
        expander_grid.attach(label, 0, 2, 1, 1)

        context_store = Gtk.ListStore(str, str)
        self.context = Gtk.ComboBox.new()
        self.context.connect('changed', self.on_priority_project_context_changed)
        self.context.set_model(context_store)
        cell1 = Gtk.CellRendererText()
        self.context.pack_start(cell1, True)
        self.context.add_attribute(cell1, 'text', 0)
        expander_grid.attach(self.context, 1, 2, 1, 1)

        box = Gtk.Box.new(Gtk.Orientation.VERTICAL, 5)
        self.grid.attach(box, 1, 0, 1, 2)

        button_add = Gtk.Button.new_with_label(_('Add task'))
        button_add.connect('clicked', self.on_button_add_clicked)
        box.add(button_add)

        button_edit = Gtk.Button.new_with_label(_('Edit task'))
        button_edit.connect('clicked', self.on_button_edit_clicked)
        box.add(button_edit)

        button_remove = Gtk.Button.new_with_label(_('Remove task'))
        button_remove.connect('clicked', self.on_button_remove_clicked)
        box.add(button_remove)

        button_clear = Gtk.Button.new_with_label(_('Clear tasks'))
        button_clear.connect('clicked', self.on_button_clear_clicked)
        box.add(button_clear)

    def on_priority_project_context_changed(self, widget):
        priority = get_selected_value_in_combo(self.priority)
        if priority == -1 or priority is None:
            priority = None
        else:
            priority = chr(priority + 65)
        project = get_selected_value_in_combo(self.project)
        if project == '-' or project is None:
            project = None
        context = get_selected_value_in_combo(self.context)
        if context == '-' or context is None:
            context = None
        self.todos.filter(priority, project, context)

    def on_toggled(self, widget):
        list_of_todos = self.todos.get_items()
        results = todotxtio.search(list_of_todos, contexts=self.contexts.get_items(), projects=self.projects.get_items())

    def on_button_clear_clicked(self, widget):
        self.todos.clear()

    def on_button_add_clicked(self, widget):
        addTodoDialog = AddTodoDialog()
        if addTodoDialog.run() == Gtk.ResponseType.ACCEPT:
            todo = addTodoDialog.get_task()
            self.todos.add_item(todo)
        addTodoDialog.destroy()

    def on_button_edit_clicked(self, widget):
        selected = self.todos.get_selected()
        if selected:
            todo = selected.get_todo()
            addTodoDialog = AddTodoDialog(todo)
            if addTodoDialog.run() == Gtk.ResponseType.ACCEPT:
                todo = addTodoDialog.get_task()
                self.todos.set_selected(todo)
            addTodoDialog.destroy()

    def on_button_remove_clicked(self, widget):
        selected = self.todos.get_selected()
        if selected:
            todo = selected.get_todo()
            self.todos.remove_item(todo)

    def load(self):
        configuration = Configuration()
        preferences = configuration.get('preferences')
        projects = preferences['projects']
        contexts = preferences['contexts']
        project_store = self.project.get_model()
        project_store.clear()
        project_store.append(['-', '-'])
        if projects:
            for project in projects:
                project_store.append([project, project])
        self.project.set_model(project_store)
        context_store = self.context.get_model()
        context_store.clear()
        context_store.append(['-', '-'])
        if contexts:
            for context in contexts:
                context_store.append([context, context])
        self.context.set_model(context_store)
        select_value_in_combo(self.priority, -1)
        select_value_in_combo(self.project, '-')
        select_value_in_combo(self.context, '-')

        todo_file = Path(os.path.expanduser(preferences['todo-file']))
        if not todo_file.exists():
            if not todo_file.parent.exists():
                os.makedirs(todo_file.parent)
            todo_file.touch()
        self.todo_file = todo_file.as_posix()
        self.load_todos()

    def load_todos(self):
        list_of_todos = todotxtio.from_file(self.todo_file)
        self.todos.add_all(list_of_todos)

    def save(self):
        todotxtio.to_file(self.todo_file, self.todos.get_items())

    def filter(self):
        active_projects = self.projects.get_active_items()
        active_contexts = self.contexts.get_active_items()
        print(active_projects, active_contexts)


if __name__ == '__main__':
    listTodos = ListTodos()
    response = listTodos.run()
    if response == Gtk.ResponseType.ACCEPT:
        listTodos.save()
    listTodos.destroy()

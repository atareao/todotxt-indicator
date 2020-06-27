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

import datetime

import gi
from basedialog import BaseDialog
from check_calendar import CheckCalendar
from config import _
from configurator import Configuration
from gi.repository import Gtk
from list_box_check import ListBoxCheck
from todotxtio import todotxtio

try:
    gi.require_version("Gtk", "3.0")
except Exception as e:
    print(e)
    exit(-1)


def string2bool(value):
    if value.lower() in ["true", "yes", "y", "1"]:
        return True
    return False


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


class AddTodoDialog(BaseDialog):
    """Docstring for AddTodoDialog. """

    def __init__(self, title, todo_item=None):
        """TODO: to be defined. """
        BaseDialog.__init__(
            self, title, None, ok_button=True, cancel_button=True
        )
        self.todo_item = todo_item
        if todo_item:
            self.text.set_text(todo_item.text)
            if todo_item.priority:
                select_value_in_combo(
                    self.priority, ord(todo_item.priority) - 65
                )
            else:
                select_value_in_combo(self.priority, -1)
            if todo_item.projects:
                self.projects.set_active_items(todo_item.projects)
            if todo_item.contexts:
                self.contexts.set_active_items(todo_item.contexts)
            for key in todo_item.tags:
                for tag_widget in self.tags:
                    if tag_widget.name == key:
                        if type(tag_widget) == CheckCalendar:
                            tag_widget.set_date(todo_item.tags[key])
                        elif type(tag_widget) == Gtk.CheckButton:
                            tag_widget.set_active(
                                string2bool(todo_item.tags[key])
                            )
                        else:
                            tag_widget.set_text(todo_item.tags[key])
                        break
        else:
            select_value_in_combo(self.priority, -1)

    def init_ui(self):
        BaseDialog.init_ui(self)

        label = Gtk.Label.new(_("Text:"))
        label.set_property("halign", Gtk.Align.START)
        self.grid.attach(label, 0, 0, 1, 1)

        self.text = Gtk.Entry.new()
        self.text.set_hexpand(True)
        self.grid.attach(self.text, 1, 0, 1, 1)

        label = Gtk.Label.new(_("Priority"))
        label.set_property("halign", Gtk.Align.START)
        self.grid.attach(label, 0, 1, 1, 1)

        priority_store = Gtk.ListStore(str, int)
        priority_store.append(["-", -1])
        for i in range(0, 26):
            priority_store.append([chr(i + 65), i])
        self.priority = Gtk.ComboBox.new()
        self.priority.set_model(priority_store)
        cell1 = Gtk.CellRendererText()
        self.priority.pack_start(cell1, True)
        self.priority.add_attribute(cell1, "text", 0)
        self.grid.attach(self.priority, 1, 1, 1, 1)

        configuration = Configuration()
        preferences = configuration.get("preferences")
        projects = preferences["projects"]
        contexts = preferences["contexts"]
        tags = preferences["tags"]
        show_hidden_tags = preferences["show-hidden-tags"]
        self.editable_hidden_tags = show_hidden_tags
        posv = 1
        self.projects = None
        self.contexts = None
        self.tags = []
        if projects:
            posv += 1
            label = Gtk.Label.new(_("Select project(s):"))
            label.set_halign(Gtk.Align.START)
            label.set_valign(Gtk.Align.START)
            self.grid.attach(label, 0, posv, 1, 1)

            self.projects = ListBoxCheck(projects)
            self.projects.set_min_content_height(75)
            self.projects.set_vexpand(True)
            self.grid.attach(self.projects, 1, posv, 1, 1)
        if contexts:
            posv += 1
            label = Gtk.Label.new(_("Select context(s):"))
            label.set_halign(Gtk.Align.START)
            label.set_valign(Gtk.Align.START)
            self.grid.attach(label, 0, posv, 1, 1)

            self.contexts = ListBoxCheck(contexts)
            self.contexts.set_vexpand(True)
            self.contexts.set_min_content_height(75)
            self.grid.attach(self.contexts, 1, posv, 1, 1)
        for tag in tags:
            if tag["name"] in ("started_at", "total_time") and not show_hidden_tags:
                continue
            posv += 1
            label = Gtk.Label.new(tag["name"] + ": ")
            label.set_halign(Gtk.Align.START)
            self.grid.attach(label, 0, posv, 1, 1)

            if tag["type"] == "date":
                label.set_valign(Gtk.Align.START)
                tag_widget = CheckCalendar()
            elif tag["type"] == "boolean":
                tag_widget = Gtk.CheckButton.new()
            else:
                tag_widget = Gtk.Entry.new()
            tag_widget.name = tag["name"]
            self.tags.append(tag_widget)
            self.grid.attach(self.tags[len(self.tags) - 1], 1, posv, 1, 1)

    def get_task(self):
        """TODO: Docstring for get_task.
        :returns: TODO

        """
        text = self.text.get_text()
        if not text:
            text = _("Empty")
        if not self.todo_item:
            creation_date = datetime.datetime.now().strftime("%Y-%m-%d")
            self.todo_item = todotxtio.Todo(
                text=text, creation_date=creation_date
            )
        else:
            self.todo_item.text = text
        priority = get_selected_value_in_combo(self.priority)
        if priority > -1:
            self.todo_item.priority = chr(priority + 65)
        if self.projects:
            self.todo_item.projects = self.projects.get_active_items()
        if self.contexts:
            self.todo_item.contexts = self.contexts.get_active_items()

        tags = {}
        if self.tags:
            for tag in self.tags:
                name = tag.name
                if type(tag) == CheckCalendar:
                    value = tag.get_date()
                elif type(tag) == Gtk.CheckButton:
                    value = str(tag.get_active())
                else:
                    value = tag.get_text()
                if value:
                    tags[name] = value

        if not self.editable_hidden_tags:
            tags["started_at"] = self.todo_item.tags.get("started_at", "0")
            tags["total_time"] = self.todo_item.tags.get("total_time", "0")
        self.todo_item.tags = tags
        return self.todo_item


if __name__ == "__main__":
    addTodoDialog = AddTodoDialog("Sample")
    response = addTodoDialog.run()
    if response == Gtk.ResponseType.ACCEPT:
        task = addTodoDialog.get_task()
    else:
        task = None
    addTodoDialog.destroy()
    if task:
        addTodoDialog = AddTodoDialog(task)
        response = addTodoDialog.run()
        if response == Gtk.ResponseType.ACCEPT:
            task = addTodoDialog.get_task()
        addTodoDialog.destroy()

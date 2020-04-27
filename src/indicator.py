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
    gi.require_version('Gdk', '3.0')
    gi.require_version('AppIndicator3', '0.1')
    gi.require_version('GdkPixbuf', '2.0')
    gi.require_version('Keybinder', '3.0')
except Exception as e:
    print(e)
    exit(-1)
from gi.repository import Keybinder
from gi.repository import Gtk
from gi.repository import Gdk
from gi.repository import GLib
from gi.repository import AppIndicator3
from gi.repository import GdkPixbuf
import sys
import os
import re
import webbrowser
import datetime
from pathlib import Path
from config import _
from graph import Graph
from preferences import Preferences
import config
from configurator import Configuration
from add_todo import AddTodoDialog
from list_todos import ListTodos
import todotxtio.todotxtio as todotxtio


class Indicator(object):

    def __init__(self):
        self.indicator = AppIndicator3.Indicator.new(
            'tasker',
            'tasker',
            AppIndicator3.IndicatorCategory.APPLICATION_STATUS)
        self.load_preferences()
        self.indicator.set_menu(self.build_menu())
        self.indicator.set_label('', '')
        self.indicator.set_status(AppIndicator3.IndicatorStatus.ACTIVE)
        self.set_icon(True)
        self.load_todos()
        Keybinder.init()
        Keybinder.bind('<Super><Ctrl>T', self.callback)
        Gtk.main()

    def callback(self, widget):
        addTodoDialog = AddTodoDialog()
        if addTodoDialog.run() == Gtk.ResponseType.ACCEPT:
            todo = addTodoDialog.get_task()
            list_of_todos = todotxtio.from_file(self.todo_file)
            for atodo in list_of_todos:
                if todo.text == atodo.text:
                    return
            list_of_todos.append(todo)
            todotxtio.to_file(self.todo_file, list_of_todos)
            self.load_todos()
        addTodoDialog.destroy()

    def set_icon(self, active=True):
        if active:
            if self.theme_light:
                icon = config.ICON_ACTIVED_LIGHT
            else:
                icon = config.ICON_ACTIVED_DARK
        else:
            if self.theme_light:
                icon = config.ICON_PAUSED_LIGHT
            else:
                icon = config.ICON_PAUSED_DARK
        self.indicator.set_icon(icon)

    def load_preferences(self):
        self.configuration = Configuration()
        preferences = self.configuration.get('preferences')
        self.theme_light = preferences['theme-light']
        self.todos = preferences['todos']
        todo_file = Path(os.path.expanduser(preferences['todo-file']))
        if not todo_file.exists():
            if not todo_file.parent.exists():
                os.makedirs(todo_file.parent)
            todo_file.touch()
        self.todo_file = todo_file.as_posix()
        self.projects = preferences['projects']
        contexts = preferences['contexts']
        tags = preferences['tags']
        self.filter_projects = preferences.get('filter-projects', False)
        self.last_filtered_projects = preferences.get('last-filtered-projects', [])
        list_of_todos = todotxtio.from_file(self.todo_file)
        pattern = r'^\d{4}-\d{2}-\d{2}$'
        for todo in list_of_todos:
            for aproject in todo.projects:
                if aproject not in self.projects:
                    self.projects.append(aproject)
            for acontext in todo.contexts:
                if acontext not in contexts:
                    contexts.append(acontext)
            for atag in todo.tags:
                if atag not in [tag['name'] for tag in tags]:
                    if re.search(pattern, todo.tags[atag]):
                        tags.append({'name': atag, 'type': 'date'})
                    elif todo.tags[atag].lower() in [ 'true', 'false']:
                        tags.append({'name': atag, 'type': 'boolean'})
                    elif todo.tags[atag].lower() in [ 'true', 'false']:
                        tags.append({'name': atag, 'type': 'boolean'})
                    else:
                        tags.append({'name': atag, 'type': 'string'})
        preferences['projects'] = self.projects
        preferences['contexts'] = contexts
        preferences['tags'] = tags
        self.configuration.set('preferences', preferences)
        self.configuration.save()
        self.set_icon(True)

    def on_popped(self, widget, display):
        pass

    def get_project_showed(self, ):
        projects_menuitems_actives = \
            list(filter(lambda item: item.get_active(), self.menu_filter_projects.get_submenu().get_children()))
        return [menu_item.get_label() for menu_item in projects_menuitems_actives]

    def set_filter_project_label(self):
        projects_menuitems = self.menu_filter_projects.get_submenu().get_children()
        projects_menuitems_actives = self.get_project_showed()
        projects_sel = _('All')
        if len(projects_menuitems) != len(projects_menuitems_actives):
            projects_sel = ', '.join(projects_menuitems_actives)
            if projects_sel == '':
                projects_sel = _('Select one to show tasks')
        self.menu_filter_projects.set_label(projects_sel)

    def on_menu_filter_project_toggled(self, widget, i):
        self.set_filter_project_label()
        self.load_todos()
        preferences = self.configuration.get('preferences')
        preferences['last-filtered-projects'] = self.get_project_showed()
        self.configuration.set('preferences', preferences)
        self.configuration.save()

    def on_menu_todo_toggled(self, widget):
        list_of_todos = todotxtio.from_file(self.todo_file)
        list_of_todos[widget.file_index].completed = widget.get_active()
        if widget.get_active():
            list_of_todos[widget.file_index].completion_date = creation_date = datetime.datetime.now().strftime('%Y-%m-%d')
        else:
            list_of_todos[widget.file_index].completion_date = None
        todotxtio.to_file(self.todo_file, list_of_todos)

    def sort(self, todo):
        if todo.priority:
            order = '000' + str(ord(todo.priority.upper()))
            return order[-3:] + todo.text.lower()
        return '999' + todo.text.lower()

    def load_todos(self):
        list_of_todos = todotxtio.from_file(self.todo_file)
        list_of_todos.sort(reverse=False, key=self.sort)

        while self.todos > len(self.menu_todos):
            self.menu_todos.append(Gtk.CheckMenuItem.new_with_label(''))
        for i in range(0, min(len(list_of_todos), self.todos)):
            if list_of_todos[i].priority:
                text = '({}) {}'.format(list_of_todos[i].priority, list_of_todos[i].text)
            else:
                text = list_of_todos[i].text
            self.menu_todos[i].file_index = i
            self.menu_todos[i].set_label(text)
            self.menu_todos[i].set_active(list_of_todos[i].completed)
            self.menu_todos[i].connect('toggled', self.on_menu_todo_toggled)
            if self.filter_projects:
                if not set(list_of_todos[i].projects).isdisjoint(self.get_project_showed()) or \
                not list_of_todos[i].projects:
                    self.menu_todos[i].show()
                else:
                    self.menu_todos[i].hide()
            else:
                self.menu_todos[i].show()
        if len(list_of_todos) < self.todos:
            for i in range(len(list_of_todos), self.todos):
                self.menu_todos[i].hide()

    def build_menu(self):
        menu = Gtk.Menu()
        menu.connect('draw', self.on_popped)

        if self.filter_projects:
            self.menu_filter_projects = Gtk.MenuItem.new_with_label('')
            self.menu_filter_projects.set_submenu(self.get_filter_project_menu())
            self.set_filter_project_label()
            menu.append(self.menu_filter_projects)
            menu.append(Gtk.SeparatorMenuItem())

        self.menu_todos = []
        for i in range(0, self.todos):
            self.menu_todos.append(Gtk.CheckMenuItem.new_with_label(''))
            menu.append(self.menu_todos[i])

        menu.append(Gtk.SeparatorMenuItem())

        menu_add_todo = Gtk.MenuItem.new_with_label(_('Add task'))
        menu_add_todo.connect('activate', self.on_menu_add_todo_activate)
        menu.append(menu_add_todo)

        menu_list_todos = Gtk.MenuItem.new_with_label(_('Tasks'))
        menu_list_todos.connect('activate', self.on_menu_list_todos_activate)
        menu.append(menu_list_todos)

        # menu.append(Gtk.SeparatorMenuItem())
        # menu_show_statistics = Gtk.MenuItem.new_with_label(
        #     _('Statistics'))
        # menu_show_statistics.connect('activate', self.show_statistics)
        # menu.append(menu_show_statistics)

        menu.append(Gtk.SeparatorMenuItem())

        menu_preferences = Gtk.MenuItem.new_with_label(_('Preferences'))
        menu_preferences.connect('activate', self.show_preferences)
        menu.append(menu_preferences)

        menus_help = Gtk.MenuItem.new_with_label(_('Help'))
        menus_help.set_submenu(self.get_help_menu())
        menu.append(menus_help)

        menu.append(Gtk.SeparatorMenuItem())

        menu_quit = Gtk.MenuItem. new_with_label(_('Quit'))
        menu_quit.connect('activate', self.quit)
        menu.append(menu_quit)
        menu.show_all()
        return menu

    def on_menu_list_todos_activate(self, widget):
        listTodos = ListTodos()
        if listTodos.run() == Gtk.ResponseType.ACCEPT:
            listTodos.save()
            self.load_todos()
        listTodos.destroy()

    def on_menu_add_todo_activate(self, widget):
        addTodoDialog = AddTodoDialog()
        if addTodoDialog.run() == Gtk.ResponseType.ACCEPT:
            todo = addTodoDialog.get_task()
            list_of_todos = todotxtio.from_file(self.todo_file)
            for atodo in list_of_todos:
                if todo.text == atodo.text:
                    return
            list_of_todos.append(todo)
            todotxtio.to_file(self.todo_file, list_of_todos)
            self.load_todos()
        addTodoDialog.destroy()

    def show_change(self, widget):
        change = Change()
        response = change.run()
        change.destroy()

    def show_preferences(self, widget):
        widget.set_sensitive(False)
        preferences = Preferences()
        response = preferences.run()
        if response == Gtk.ResponseType.ACCEPT:
            preferences.save()
            self.load_preferences()
            self.set_icon(True)
        preferences.destroy()
        widget.set_sensitive(True)

    def show_statistics(self, widget):
        widget.set_sensitive(False)

        title = _('Tasker')
        subtitle = _('Tasks statistics')
        configuration = Configuration()
        preferences = self.configuration.get('preferences')

        mc = CURRENCIES[self.main_currency]
        currencies = []
        for i in range(0, 5):
            currencies.append(CURRENCIES[self.currencies[i]])
        days = []
        c0 = []
        c1 = []
        c2 = []
        c3 = []
        c4 = []
        for aday in self.exchange.data:
            days.append(aday['date'])
            mc = aday[self.main_currency.lower()]
            c0.append(round(aday[self.currencies[0].lower()] / mc))
            c1.append(round(aday[self.currencies[1].lower()] / mc))
            c2.append(round(aday[self.currencies[2].lower()] / mc))
            c3.append(round(aday[self.currencies[3].lower()] / mc))
            c4.append(round(aday[self.currencies[4].lower()] / mc))

        graph = Graph(title, subtitle, currencies, days, c0, c1, c2, c3, c4)
        graph.run()
        graph.destroy()
        widget.set_sensitive(True)

    def get_filter_project_menu(self):
        filter_menu = Gtk.Menu()

        for i in range(0, len(self.projects)):
            project_item = Gtk.CheckMenuItem.new_with_label(self.projects[i])
            project_item.set_active(1 if self.projects[i] in self.last_filtered_projects else 0)
            project_item.connect('toggled', self.on_menu_filter_project_toggled, i)
            filter_menu.append(project_item)
        return filter_menu

    def get_help_menu(self):
        help_menu = Gtk.Menu()

        homepage_item = Gtk.MenuItem.new_with_label(_('Homepage'))
        homepage_item.connect(
            'activate',
            lambda x: webbrowser.open(
                'http://www.atareao.es/aplicacion/tasker/'))
        help_menu.append(homepage_item)

        help_item = Gtk.MenuItem.new_with_label(_('Get help online...'))
        help_item.connect(
            'activate',
            lambda x: webbrowser.open(
                'http://www.atareao.es/aplicacion/tasker/'))
        help_menu.append(help_item)

        translate_item = Gtk.MenuItem.new_with_label(_(
            'Translate this application...'))
        translate_item.connect(
            'activate',
            lambda x: webbrowser.open(
                'http://www.atareao.es/aplicacion/tasker/'))
        help_menu.append(translate_item)

        bug_item = Gtk.MenuItem.new_with_label(_('Report a bug...'))
        bug_item.connect(
            'activate',
            lambda x: webbrowser.open('https://github.com/atareao\
/tasker/issues'))
        help_menu.append(bug_item)

        help_menu.append(Gtk.SeparatorMenuItem())

        twitter_item = Gtk.MenuItem.new_with_label(_('Found me in Twitter'))
        twitter_item.connect(
            'activate',
            lambda x: webbrowser.open('https://twitter.com/atareao'))
        help_menu.append(twitter_item)
        #
        github_item = Gtk.MenuItem.new_with_label(_('Found me in GitHub'))
        github_item.connect(
            'activate',
            lambda x: webbrowser.open('https://github.com/atareao'))
        help_menu.append(github_item)

        mastodon_item = Gtk.MenuItem.new_with_label(_('Found me in Mastodon'))
        mastodon_item.connect(
            'activate',
            lambda x: webbrowser.open('https://mastodon.social/@atareao'))
        help_menu.append(mastodon_item)

        about_item = Gtk.MenuItem.new_with_label(_('About'))
        about_item.connect('activate', self.menu_about_response)

        help_menu.append(Gtk.SeparatorMenuItem())

        help_menu.append(about_item)
        return help_menu

    def menu_about_response(self, widget):
        widget.set_sensitive(False)
        ad = Gtk.AboutDialog()
        ad.set_name(config.APPNAME)
        ad.set_version(config.VERSION)
        ad.set_copyright('Copyrignt (c) 2020\nLorenzo Carbonell')
        ad.set_comments(_('Tasker'))
        ad.set_license('''
Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:
The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.
THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.''')
        ad.set_website('')
        ad.set_website_label('http://www.atareao.es')
        ad.set_authors(['Lorenzo Carbonell Cerezo <a.k.a. atareao>'])
        ad.set_translator_credits('Lorenzo Carbonell Cerezo <a.k.a. atareao>')
        ad.set_documenters(['Lorenzo Carbonell Cerezo <a.k.a. atareao>'])
        ad.set_artists(['Freepik <https://www.flaticon.com/authors/freepik>'])
        ad.set_logo(GdkPixbuf.Pixbuf.new_from_file(config.ICON))
        ad.set_icon(GdkPixbuf.Pixbuf.new_from_file(config.ICON))
        ad.set_program_name(config.APPNAME)

        monitor = Gdk.Display.get_primary_monitor(Gdk.Display.get_default())
        scale = monitor.get_scale_factor()
        monitor_width = monitor.get_geometry().width / scale
        monitor_height = monitor.get_geometry().height / scale
        width = ad.get_preferred_width()[0]
        height = ad.get_preferred_height()[0]
        ad.move((monitor_width - width)/2, (monitor_height - height)/2)

        ad.run()
        ad.destroy()
        widget.set_sensitive(True)

    def quit(self, menu_item):
        Gtk.main_quit()
        # If Gtk throws an error or just a warning, main_quit() might not
        # actually close the app
        sys.exit(0)


def main():
    Indicator()


if __name__ == '__main__':
    main()

from kivy.lang import Builder
from kivy.app import App
from kivy.uix.relativelayout import RelativeLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.layout import Layout
from kivy.properties import NumericProperty, ObjectProperty
from kivy.core.window import Window
from kivy.uix.image import Image
from kivy.uix.label import Label
from kivy.uix.behaviors import ButtonBehavior
from kivy.graphics import Color, Line

import numpy as np
import math

from perm_solver import Game

# red, green, blue, neutral
label_angles = {
  (1,0,0,0):(0,0,0),
  (0,1,0,0):(0,0,0),
  (0,0,1,0):(0,0,0),
  (0,0,0,1):(0,0,0),

  (1,0,1,0):(120,0,-60),
  (1,1,0,0):(60,-120,0),
  (1,0,0,1):(90,0,0),
  (0,1,1,0):(0,-180,0),
  (0,1,0,1):(0,90,0),
  (0,0,1,1):(0,0,90),

  (1,1,1,0):(90,-150,-30),
  (1,1,0,1):(90,-150,-30),
  (1,0,1,1):(90,-150,-30),
  (0,1,1,1):(90,-150,-30),
  }

game = Game()
pyramid_widgets = []
grid_widgets = [];

class ScrollViewFixedAR(ScrollView, Layout):
    # Scroll view with width fitting the screen, content at a fixed aspect ratio.
    def do_layout(self, *args):
        for child in self.children:
            self.apply_ratio(child)
        super(ScrollViewFixedAR, self).do_layout()

    def apply_ratio(self, child):
        # with of content = width of view
        child.size_hint_x = 1

        # height of content bigger than height of view
        view_ratio = float(self.width)/float(self.height)
        child.size_hint_y = view_ratio / child.aspect_ratio
        child.pos_hint = {"center_x": .5, "center_y": .5}

class PotionSetGraphic(ButtonBehavior, Image, FloatLayout):
  # A PotionSetGraphic is the graphic representation of a list of possible potions.
  def __init__(self, *args, **kwargs):
    kwargs['source'] = '../img/unknown.png'
    kwargs['allow_stretch'] = True
    super(PotionSetGraphic, self).__init__(*args, **kwargs)

  def set_potion_set(self,potion_set):
    print "set_potion_set"
    self.potion_set = potion_set.copy()
    active_colors = np.sum(self.potion_set,1) > 0;
    minus = self.potion_set[:3,0] & ~self.potion_set[:3,1]
    plus  = self.potion_set[:3,1] & ~self.potion_set[:3,0]

    if np.sum(active_colors) == 4:
      # grey unknown marker if all four colors are possible
      self.source = '../img/unknown.png'
    else:
      # colored marker if colors narrowed down to three or fewer
      colorlist = ['red','green','blue','neutral']
      filename = '../img/'
      for c in range(0,4):
        if active_colors[c]:
          filename = filename + colorlist[c] + '_'
      filename = filename[:-1]+'.png'
      self.source = filename
      self.clear_widgets()

    # label radius for one, two, or three options
    pos_radius  = (0,     0.25, 0.25, 0)[np.sum(active_colors)-1]
    size        = (0.6,  0.25, 0.25, 0.8)[np.sum(active_colors)-1]

    if label_angles.has_key(tuple(active_colors)):
      for k in range(0,3):
        x = pos_radius * math.cos(math.radians(label_angles[tuple(active_colors)][k]))
        y = pos_radius * math.sin(math.radians(label_angles[tuple(active_colors)][k]))
        pos_hint = pos_hint={'center_x':0.5+x,'center_y':0.5+y}
        if minus[k]:
          label = Image(source='../img/minus.png', size_hint=(size,size), pos_hint=pos_hint)
          self.add_widget(label)
        elif plus[k]:
          label = Image(source='../img/plus.png', size_hint=(size,size), pos_hint=pos_hint)
          self.add_widget(label)




class Result(PotionSetGraphic):
  # A Result is the graphical result of mixing labels A and B
  def __init__(self, *args, **kwargs):
    self.label_a = kwargs['label_a']
    self.label_b = kwargs['label_b']
    super(Result, self).__init__(*args, **kwargs)
    self.bind(on_press=result_callback)




class Pallet(PotionSetGraphic):
  # A Pallet is the graphical representation of a set of potion results.
  def __init__(self, *args, **kwargs):
    super(Pallet, self).__init__(*args, **kwargs)
    self.bind(on_press=pallet_callback)




class Ingredient(ButtonBehavior, Image):
  # An Ingredient is the graphic representation of an ingredient.
  def __init__(self, *args, **kwargs):
    self.label = kwargs['label']
    colorset = [(128,0,128), (34,139,34), (139,69,19), (255,215,0), (65,105,225), (210,180,140), (178,34,34), (112,128,144)]
    rgba = []
    for c in colorset:
      x = np.array(c);
      x = x/np.linalg.norm(x);
      rgba.append((x[0],x[1],x[2],1))

    kwargs['color'] = rgba[self.label]
    kwargs['source'] = '../img/ingredient.png'
    kwargs['allow_stretch'] = True
    super(Ingredient, self).__init__(*args, **kwargs)
    self.bind(on_press=ingredient_callback)




class Labeling(Image):
  def __init__(self, *args, **kwargs):
    kwargs['color'] = (0.2,0.2,0.2,1.0)
    kwargs['source'] = '../img/white_rect.png'
    kwargs['allow_stretch'] = True
    self.formula = kwargs['formula']
    self.ingredient = kwargs['ingredient']
    super(Labeling, self).__init__(*args, **kwargs)
  def mark_false(self):
    self.source = '../img/red.png'




def result_callback(instance):
    # print 'Result of <%s> and <%s> marked as:' % (instance.label_a, instance.label_b)
    # print instance.parent.pallet_potion_set
    game.RequireFromMixture(instance.label_a, instance.label_b, instance.parent.pallet_potion_set)
    for p in pyramid_widgets:
      p.set_potion_set(game.MixLabels(p.label_a, p.label_b))

    matrix = game.MatchTable()
    for m in grid_widgets:
      if not matrix[m.ingredient, m.formula]:
        m.mark_false()
        print m.size
      
    print 'Remaining Solutions:', game.NumberSolutions()
    instance.parent.solutions_label.text = "{:>6} Solutions".format(game.NumberSolutions())

    print instance.parent.size


def pallet_callback(instance):
    instance.parent.pallet_potion_set = instance.potion_set
    pass

def ingredient_callback(instance):
    # print 'Ingredient <%s>  marked as:' % (instance.label)
    print instance.parent.pallet_potion_set
    game.RequireFromIngredient(instance.label, instance.parent.pallet_potion_set)
    for p in pyramid_widgets:
      p.set_potion_set(game.MixLabels(p.label_a, p.label_b))

    matrix = game.MatchTable()
    for m in grid_widgets:
      if not matrix[m.ingredient, m.formula]:
        m.mark_false()

    print 'Remaining Solutions:', game.NumberSolutions()
    instance.parent.solutions_label.text = "{:>6} Solutions".format(game.NumberSolutions())


class AlchemistsBuddy(App):
    def build(self):

        # configure window
        window_width = 1920/2;
        Window.size = (window_width, window_width*9.0/16.0)

        # pyramid of results
        pyramid_top_x = 0.5
        pyramid_top_y = 1.0 - self.root.pyramid.result_height/2
        lower_left_x = pyramid_top_x - 3*self.root.pyramid.h_space
        lower_left_y = pyramid_top_y - 6*self.root.pyramid.v_space
        for b in range(0,8):
          for a in range(0,b):
            row = b-a-1
            x = lower_left_x + a*self.root.pyramid.h_space + row*(self.root.pyramid.h_space/2)
            y = lower_left_y + row*self.root.pyramid.v_space
            btn = Result(pos_hint={'center_x':x,'center_y':y}, label_a=a, label_b=b)
            self.root.pyramid.add_widget(btn)
            pyramid_widgets.append(btn)


        # row of ingredients
        lower_left_x = lower_left_x - self.root.pyramid.h_space/2
        lower_left_y = lower_left_y - self.root.pyramid.v_space
        for a in range(0,8):
          x = lower_left_x + a*self.root.pyramid.h_space
          height = self.root.pyramid.result_height
          ratio = self.root.pyramid.aspect_ratio
          btn = Ingredient(size_hint=(height/ratio,height), pos_hint={'center_x':x,'center_y':lower_left_y}, label=a)
          self.root.pyramid.add_widget(btn)


        # array of potion pallets
        pallet_v_space = self.root.pyramid.result_height
        pallet_h_space = self.root.pyramid.result_height/self.root.pyramid.aspect_ratio
        top_x = 0.0 + 0.5*pallet_h_space
        top_y = 1.0 - 0.5*pallet_v_space
        # true potions
        for a in range(0,3):
          for b in range(0,2):
            x = top_x + b*pallet_h_space
            y = top_y - a*pallet_v_space
            btn = Pallet(pos_hint={'center_x':x,'center_y':y})
            mixes = np.zeros((4,2),dtype='bool')
            mixes[a,b] = True
            self.root.pyramid.add_widget(btn)
            btn.set_potion_set(mixes)
        # neutral
        btn = Pallet(pos_hint={'center_x':top_x+pallet_h_space/2,'center_y':top_y-2*pallet_v_space-pallet_v_space*math.cos(math.radians(30))})
        mixes = np.zeros((4,2),dtype='bool')
        mixes[3,:] = True
        self.root.pyramid.add_widget(btn)
        btn.set_potion_set(mixes)
        # twin colors
        top_x = 1.0 - 1.5*pallet_h_space
        top_y = 1.0 - 0.5*pallet_v_space
        for a in range(0,3):
          for b in range(0,2):
            x = top_x + b*pallet_h_space
            y = top_y - a*pallet_v_space
            btn = Pallet(pos_hint={'center_x':x,'center_y':y})
            self.root.pyramid.add_widget(btn)
            mixes = np.zeros((4,2),dtype='bool')
            mixes[:3,b] = True
            mixes[a,b] = False
            btn.set_potion_set(mixes)
        # three colors
        y = top_y - 3*pallet_v_space
        for b in range(0,2):
          x = top_x + b*pallet_h_space
          btn = Pallet(pos_hint={'center_x':x,'center_y':y})
          self.root.pyramid.add_widget(btn)
          mixes = np.zeros((4,2),dtype='bool')
          mixes[:3,b] = True
          btn.set_potion_set(mixes)






        # Labeling Matrix
        grid_aspect_ratio = 16.0/9.0
        grid_fill = 0.9
        grid_width = self.root.pyramid.h_space * grid_fill
        grid_height = grid_width / grid_aspect_ratio * self.root.grid.aspect_ratio
        print grid_width/grid_height
        # grid_v_space = (1.0-grid_fill)*self.root.pyramid.h_space * self.root.grid.aspect_ratio + grid_height
        grid_v_space = grid_height / grid_fill
        # grid_v_space = self.root.pyramid.h_space / self.root.grid.aspect_ratio
        grid_wigets = []
        for formula in range(0,8):
          for ingredient in range(0,8):
            x = lower_left_x + ingredient*self.root.pyramid.h_space
            y = 1.0 - 1.5*grid_v_space - formula*grid_v_space
            # img = Labeling((result_height*self.root.aspect_ratio,result_height), pos_hint={'center_x':x,'center_y':y}, formula=formula, ingredient=ingredient)
            # h = self.root.pyramid.result_height
            # w = self.root.pyramid.result_height
            img = Labeling(size_hint=(grid_width, grid_height), pos_hint={'center_x':x,'center_y':y}, formula=formula, ingredient=ingredient)
            self.root.grid.add_widget(img)
            grid_widgets.append(img)

        # left = 
        # with self.root.grid.canvas:
        #   Color(0.7, 0.7, 0.7)
        #   Line(points=[0,0,400,400], width=4)

        number_solutions = Label(text='40320 Solutions', size_hint=(None,None), pos_hint={'x':0.6,'y':0.9}, halign='right', valign='top', strip=False)

        self.root.pyramid.solutions_label = number_solutions
        self.root.pyramid.add_widget(number_solutions)

        return self.root

AlchemistsBuddy().run()
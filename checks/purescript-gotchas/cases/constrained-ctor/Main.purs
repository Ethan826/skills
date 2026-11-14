module ConstrainedCtor.Main where

import Prelude

data Range a = Ord a => Range a a

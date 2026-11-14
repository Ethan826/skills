module AbsFromDataOrd.Main where

import Prelude

import Data.Ord (abs, signum)

size :: Int
size = abs (-3) + signum 2

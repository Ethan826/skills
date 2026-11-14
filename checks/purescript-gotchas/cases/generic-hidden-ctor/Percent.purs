module GenericHiddenCtor.Percent (Percent, percent) where

import Data.Generic.Rep (class Generic)

newtype Percent = Percent Int

derive instance Generic Percent _

percent :: Int -> Percent
percent = Percent

module FacadeHidesCtorControl.Money.Cents (Cents(..), fromInt) where

newtype Cents = Cents Int

fromInt :: Int -> Cents
fromInt = Cents

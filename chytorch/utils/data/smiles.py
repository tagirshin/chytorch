# -*- coding: utf-8 -*-
#
#  Copyright 2023 Ramil Nugmanov <nougmanoff@protonmail.com>
#  This file is part of chytorch.
#
#  chytorch is free software; you can redistribute it and/or modify
#  it under the terms of the GNU Lesser General Public License as published by
#  the Free Software Foundation; either version 3 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#  GNU Lesser General Public License for more details.
#
#  You should have received a copy of the GNU Lesser General Public License
#  along with this program; if not, see <https://www.gnu.org/licenses/>.
#
from chython import MoleculeContainer, ReactionContainer, smiles
from torch import Size
from torch.utils.data import Dataset
from typing import Dict, Union, Sequence, Optional, Type


class SMILESDataset(Dataset):
    def __init__(self, data: Sequence[str], *, canonicalize: bool = False, cache: Optional[Dict[int, bytes]] = None,
                 dtype: Union[Type[MoleculeContainer], Type[ReactionContainer]] = MoleculeContainer,
                 unpack: bool = True, ignore_stereo: bool = True, ignore_bad_isotopes: bool = False,
                 keep_implicit: bool = False, ignore_carbon_radicals: bool = False):
        """
        Smiles to chython containers on-the-fly parser dataset.
        Note: SMILES strings or coded structures can be invalid and lead to exception raising.
        Make sure you have validated input.

        :param data: smiles dataset
        :param canonicalize: do standardization (slow, better to prepare data in advance and keep in kekule form)
        :param cache: dict-like object for caching processed data. caching disabled by default.
        :param dtype: expected type of smiles (reaction or molecule)
        :param unpack: return unpacked structure or chython pack
        :param ignore_stereo: Ignore stereo data.
        :param keep_implicit: keep given in smiles implicit hydrogen count, otherwise ignore on valence error.
        :param ignore_bad_isotopes: reset invalid isotope mark to non-isotopic.
        :param ignore_carbon_radicals: fill carbon radicals with hydrogen (X[C](X)X case).
        """
        self.data = data
        self.canonicalize = canonicalize
        self.cache = cache
        self.dtype = dtype
        self.unpack = unpack
        self.ignore_stereo = ignore_stereo
        self.ignore_bad_isotopes = ignore_bad_isotopes
        self.keep_implicit = keep_implicit
        self.ignore_carbon_radicals = ignore_carbon_radicals

    def __getitem__(self, item: int) -> Union[MoleculeContainer, ReactionContainer, bytes]:
        if self.cache is not None and item in self.cache:
            s = self.cache[item]
            if self.unpack:
                return self.dtype.unpack(s)
            return s

        s = smiles(self.data[item], ignore_stereo=self.ignore_stereo, ignore_bad_isotopes=self.ignore_bad_isotopes,
                   keep_implicit=self.keep_implicit, ignore_carbon_radicals=self.ignore_carbon_radicals)
        if not isinstance(s, self.dtype):
            raise TypeError(f'invalid SMILES: {self.dtype} expected, but {type(s)} given')
        if self.canonicalize:
            s.canonicalize()

        if self.cache is not None:
            p = s.pack()
            self.cache[item] = p
            if self.unpack:
                return s
            return p
        if self.unpack:
            return s
        return s.pack()

    def __len__(self):
        return len(self.data)

    def size(self, dim):
        if dim == 0:
            return len(self)
        elif dim is None:
            return Size((len(self),))
        raise IndexError


__all__ = ['SMILESDataset']

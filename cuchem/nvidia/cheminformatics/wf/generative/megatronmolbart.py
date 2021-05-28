import logging
import numpy as np
import pandas as pd
from typing import List

import grpc
import torch
import torch.nn
import pickle
from pathlib import Path
import numpy as np
from functools import partial

from rdkit import Chem

from cuchemcommon.data import GenerativeWfDao
from cuchemcommon.data.generative_wf import ChemblGenerativeWfDao
from cuchemcommon.utils.singleton import Singleton
from cuchemcommon.workflow import BaseGenerativeWorkflow
from nvidia.cheminformatics.fingerprint import MorganFingerprint

import generativesampler_pb2
import generativesampler_pb2_grpc

logger = logging.getLogger(__name__)


class MegatronMolBART(BaseGenerativeWorkflow, metaclass=Singleton):

    def __init__(self, dao: GenerativeWfDao = ChemblGenerativeWfDao(MorganFingerprint)) -> None:
        super().__init__(dao)

        self.min_jitter_radius = 2.1
        channel = grpc.insecure_channel('megamolbart:50051')
        self.stub = generativesampler_pb2_grpc.GenerativeSamplerStub(channel)

    def find_similars_smiles(self,
                             smiles:str,
                             num_requested:int=10,
                             scaled_radius=None,
                             force_unique=False):
        radius = self._compute_radius(scaled_radius)
        spec = generativesampler_pb2.GenerativeSpec(
            model=generativesampler_pb2.GenerativeModel.MegaMolBART,
            smiles=smiles,
            radius=radius,
            numRequested=num_requested)

        result = self.stub.FindSimilars(spec)
        result = result.generatedSmiles

        generated_df = pd.DataFrame({'SMILES': result,
                                     'Generated': [True for i in range(len(result))]})
        generated_df['Generated'].iat[0] = False

        return generated_df

    def interpolate_from_smiles(self,
                                smiles:List,
                                num_points:int=10,
                                scaled_radius=None,
                                force_unique=False):

        radius = self._compute_radius(scaled_radius)

        spec = generativesampler_pb2.GenerativeSpec(
            model=generativesampler_pb2.GenerativeModel.MegaMolBART,
            smiles=smiles,
            radius=radius,
            numRequested=num_points)

        result = self.stub.Interpolate(spec)
        result = result.generatedSmiles

        generated_df = pd.DataFrame({'SMILES': result,
                                     'Generated': [True for i in range(len(result))]})
        generated_df.iat[0, 1] = False
        generated_df.iat[0, 1] = False

        return generated_df


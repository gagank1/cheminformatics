import logging

import generativesampler_pb2
import generativesampler_pb2_grpc

from megamolbart.inference import MegaMolBART


logger = logging.getLogger(__name__)


class GenerativeSampler(generativesampler_pb2_grpc.GenerativeSampler):

    def __init__(self, *args, **kwargs):
        self.megamolbart = MegaMolBART()


    def FindSimilars(self, spec, context):
        _, generated_smiles = \
                self.megamolbart.find_similars_smiles(
                    spec.smiles[0],
                    num_requested=spec.numRequested,
                    radius=spec.radius)
        return generativesampler_pb2.SmilesList(generatedSmiles=generated_smiles)

    def Interpolate(self, spec, context):

        _, generated_smiles  = self.megamolbart.interpolate_from_smiles(
                    spec.smiles,
                    num_points=spec.numRequested,
                    radius=spec.radius)
        return generativesampler_pb2.SmilesList(generatedSmiles=generated_smiles)


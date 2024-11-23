from pytomography.io.SPECT import dicom
from pytomography.algorithms import OSEM
from pytomography.projectors.SPECT import SPECTSystemMatrix
from pytomography.likelihoods import PoissonLogLikelihood


def reconstruction(file_path, main_index, lower_scatter_index=-1, upper_scatter_index=-1):
    object_meta, proj_meta = dicom.get_metadata(file_path, index_peak=main_index)

    photopeak = dicom.get_projections(file_path, index_peak=main_index)

    system_matrix = SPECTSystemMatrix(
        obj2obj_transforms = [],
        proj2proj_transforms = [],
        object_meta = object_meta,
        proj_meta = proj_meta
    )

    if lower_scatter_index >= 0 and upper_scatter_index >= 0:
        scatter = dicom.get_energy_window_scatter_estimate(file_path, index_peak=main_index,
                                                           index_lower=lower_scatter_index,
                                                           index_upper=upper_scatter_index)
        likelihood = PoissonLogLikelihood(system_matrix, photopeak, scatter)
    elif lower_scatter_index >= 0:
        scatter = dicom.get_energy_window_scatter_estimate(file_path, index_peak=main_index,
                                                           index_lower=lower_scatter_index)
        likelihood = PoissonLogLikelihood(system_matrix, photopeak, scatter)
    elif upper_scatter_index >= 0:
        scatter = dicom.get_energy_window_scatter_estimate(file_path, index_peak=main_index,
                                                           index_upper=upper_scatter_index)
        likelihood = PoissonLogLikelihood(system_matrix, photopeak, scatter)
    else:
        likelihood = PoissonLogLikelihood(system_matrix, photopeak)

    reconstruction_algorithm = OSEM(likelihood)

    reconstructed_object = reconstruction_algorithm(n_iters=1, n_subsets=8)

    return reconstructed_object
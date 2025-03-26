! PROFFAST 2 - Retrieval code for the COllaborative Carbon COlumn Network (COCCON)
! Copyright (C)   2022   Frank Hase, Karlsruhe Institut of Technology (KIT)
!
! This program is free software: you can redistribute it and/or modify
! it under the terms of the GNU General Public License version 3 as published by
! the Free Software Foundation.
!
! This program is distributed in the hope that it will be useful,
! but WITHOUT ANY WARRANTY; without even the implied warranty of
! MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
! GNU General Public License for more details.
!
! You should have received a copy of the GNU General Public License
! along with this program.  If not, see <https://www.gnu.org/licenses/>.

module globlev24

use globvar24, only: maxlev,maxams,maxavk,maxsens,maxtau

implicit none

type levels
    sequence
    real(8),dimension(maxlev) :: T_K,p_Pa,h_m
    real(8),dimension(maxlev) :: n_cbm,n_cbm_dry,colair,colair_do,colair_up
    real(8),dimension(maxlev,maxams) :: sza_rad
    real(8),dimension(maxlev,maxavk) :: sza_rad_avk
    real(8),dimension(maxlev,maxtau) :: vmr_ppmv
    real(8),dimension(maxlev,maxavk,maxsens,maxtau) :: colsens
end type

type (levels) :: lev

end module globlev24

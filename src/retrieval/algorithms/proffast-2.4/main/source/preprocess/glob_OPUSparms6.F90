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


module glob_OPUSparms6

use glob_prepro6,only : maxmeas,maxOPUSchar

implicit none

!    ' RES - resolution
!    ' HFW - high folding limit(should be sligtly less than 15798)
!    ' LWN - laser wavenumber (should be near 15798)
!    ' DAT - date
!    ' TIM - time
!    ' VEL - scanner velocity
!    ' NSS - number of scans (should be even and equal to GFW + GBW)
!    ' GFW - number good fwd scans
!    ' GBW - number of good backward scans
!    ' AQM - acquisition mode (should be DD)
!    ' HPF - high pass filter
!    ' LPF - low pass filter
!    ' TSC - scanner T
!    ' SSM - sample spacing multiplicator (should be 2)
!    ' DUR - total duration of sample recording (sec)  

type OPUS_parameters
    sequence
    character(len=maxOPUSchar) :: DAT ! date
    character(len=maxOPUSchar) :: TIM ! time
    character(len=maxOPUSchar) :: VEL ! scanner velocity ENUM!!
    character(len=maxOPUSchar) :: AQM ! acquisition mode (should be DD)
    character(len=maxOPUSchar) :: HPF ! high pass filter
    character(len=maxOPUSchar) :: LPF ! low pass filter
    integer :: NSS                    ! number of scans (should be even and equal to GFW + GBW)
    integer :: GFW                    ! number good fwd scans
    integer :: GBW                    ! number of good backward scans
    integer :: SSM                    ! sample spacing multiplicator (should be 2)
    real(8) :: RES                    ! resolution
    real(8) :: HFL                    ! high folding limit(should be sligtly less than 15798)
    real(8) :: LWN                    ! laser wavenumber (should be near 15798)
    real(8) :: TSC                    ! scanner T
    real(8) :: DUR                    ! total scan duration in sec
end type

type (OPUS_parameters) :: OPUS_parms(maxmeas)

end module glob_OPUSparms6


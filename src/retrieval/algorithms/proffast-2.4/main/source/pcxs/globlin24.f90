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

module globlin24

use globvar24, only: maxlines,maxtau

implicit none

!logical :: anysdgdec
!integer,parameter :: maxrim = 20
!integer,parameter :: maxvgt_d = 180
!integer,parameter :: maxvgt_nue = 201
!real(8),parameter :: mwextd_lbl = 5.0d0 ! extd MW bounds are extended, lines in this extended range are handled in lbl calc
!real(8) :: tauschwell_adj,slope_adj,dnue_adj ! user knobs to influence lbl calc accuracy
!real(8),dimension(3) :: T_lbl

!real(8) :: mwextd_readlines_rim ! MW bounds are extended, lines in this extended range are read

!complex,dimension(maxvgt_nue,maxvgt_d) :: voigttable

integer,parameter :: maxroi = 8
integer,parameter :: nSDV = 20  ! size of SDV lookup table (-nSDV to nSDV)
complex(8),dimension(maxroi) :: nueroi
real(8),dimension(7,-nSDV:nSDV) :: SDVtab

integer :: n_roi

type linedata
    sequence
    integer,dimension(maxtau) :: lb,rb
    !integer,dimension(max_n_mw,maxtau) :: lb_lbl,rb_lbl
    !integer,dimension(max_n_mw,maxtau) :: lb_rim,rb_rim
    ! the pointers below defina a subset of lines:
    ! these lines are located within the extended MW bounds (+-additional extension of 6 * HWHM)
    ! for all the remaining lines (if relevant) a wing approx is applied
    ! (depends on pressure + applied MW extension and therefore on ILS width)
    ! this decides whether a line gives a significant rim contribution
    ! (depends on applied MW extension and therefore on ILS width)
    integer,dimension(maxlines) :: species
    real(8),dimension(maxlines) :: nue
    !real,dimension(maxlines) :: ergniveau,kappacm,lorwidthf,lorwidths,lortdepend,pshift &
    !  ,gam2,gam2tdepend,beta,betatdepend
    logical,dimension(maxlines) :: LMdec
    real,dimension(maxlines) :: LMY,LMTK1,LMTK2
    logical,dimension(maxlines) :: SDVdec
    real,dimension(maxlines) :: gam2ratio,gam2Tdep
    real,dimension(maxlines) :: ergniveau,kappacm,lorwidthf,lorwidths,lortdepend,pshift
    !real(8),dimension(maxlines) :: gauhwhm
    !real,dimension(maxlines) :: vnorm_coeffa,vnorm_coeffb,vnorm_coeffc
    !wert = coeff(1) + x * coeff(2) + x * x * coeff(3)
    ! x = (T - Tref) / (Tmax - Tmin)
end type

type (linedata) :: lines


end module globlin24

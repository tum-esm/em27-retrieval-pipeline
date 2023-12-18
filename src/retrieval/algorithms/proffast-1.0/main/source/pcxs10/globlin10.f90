!     Last change:  BLA   8 Jan 2017    7:52 pm
module globlin10

use globvar10, only: maxlines,maxtau

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



type linedata
    sequence
    integer,dimension(maxtau) :: lb,rb
    !integer,dimension(max_n_mw,maxtau) :: lb_lbl,rb_lbl
    !integer,dimension(max_n_mw,maxtau) :: lb_rim,rb_rim
    ! the pointers below defina a subset of lines:
    ! these lines are located within the extended MW bounds (+-additional extension of 6 * HWHM)
    ! for all the remaining lines (if relevant) a wing approx is applied
    ! (depends on pressure + applied MW extension and therefore on ILS width)
    !logical,dimension(maxlines) :: sdgdec
    ! this decides whether a line gives a significant rim contribution
    ! (depends on applied MW extension and therefore on ILS width)
    integer,dimension(maxlines) :: species
    real(8),dimension(maxlines) :: nue
    !real,dimension(maxlines) :: ergniveau,kappacm,lorwidthf,lorwidths,lortdepend,pshift &
    !  ,gam2,gam2tdepend,beta,betatdepend,YLM,LMTK1,LMTK2
    real,dimension(maxlines) :: ergniveau,kappacm,lorwidthf,lorwidths,lortdepend,pshift
    !real(8),dimension(maxlines) :: gauhwhm
    !real,dimension(maxlines) :: vnorm_coeffa,vnorm_coeffb,vnorm_coeffc
    !wert = coeff(1) + x * coeff(2) + x * x * coeff(3)
    ! x = (T - Tref) / (Tmax - Tmin)
end type

type (linedata) :: lines


end module globlin10

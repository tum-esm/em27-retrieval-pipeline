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

module glob_prepro4

implicit none

character(len=1),parameter::pathstr="/"         ! Windows or Linux
integer,parameter :: maxblock = 40
integer,parameter :: maxblength = 50000
integer,parameter :: nzf = 32 ! oversampling of sinc kernel on fft grid
integer,parameter :: nconv = 400 ! conv range (-nconv...+nconv) for resampling on fft grid
integer,parameter :: maxmeas = 100000
integer,parameter :: maxOPUSchar = 64
integer,parameter :: nsmooth = 400 ! iterations for DC correction of IFG
integer,parameter :: lengthcharmeas = 300   ! supported name length of measured file (path + name)
integer,parameter :: minfilesize = 100000 ! if smaller, assume OPUS file is truncated

real(8),parameter :: pi = 3.141592653589793d0
real(8),parameter :: gradtorad = pi / 180.0d0
real(8),parameter :: radtograd = 180.0d0 / pi
real(8),parameter :: nuelas = 15798.0d0
real(8),parameter :: semiFOV = 2.36e-3 !0.5 * 0.6 mm / 127 mm

real(8),parameter :: phasa1max = 1.0d-3!1.0d-4
real(8),parameter :: phasa2max = 1.0d-7!1.0d-9
real(8),parameter :: phasa3max = 1.0d-11!1.0d-13

real(8),parameter :: nuersstart = 4500.0d0
real(8),parameter :: nuersstop = 14000.0d0
real(8),parameter :: nuersstart2 = 3800.0d0
real(8),parameter :: nuersstop2 = 5200.0d0

logical :: obsfixdec,checkoutdec,quietrundec
character(len=300) :: infotext,diagoutpath,binoutpath
character(len=30) :: obslocation
integer :: mpowFFT,ifgradius,maxifg,maxspc,maxspcrs
integer :: nmeas,nsinc,TCCONkind !nsinc: width of sinc kernel on oversampled fft grid -nsinc...+nsinc
real(8) :: OPDmax
real :: ILSapo,ILSapo2,ILSphas,ILSphas2,DCmin,DCvar,obsfixlatdeg,obsfixlondeg &
  ,obsfixaltkm,toffseth_UT

end module glob_prepro4

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


!====================================================================
!
! This program is for the preprocessing of COCCON measurements.
! It performs quality checks, DC-correction, FFT and phase correction,
! and a resampling of the spectrum to a minimally sampled grid.
!
! This code has been created by Frank Hase (frank.hase@kit.edu) and
! Darko Dubravica (darko.dubravica@kit.edu), both affiliated with KIT
! in the framework of ESA's COCCON-PROCEEDS project.
!
!====================================================================

program preprocess4

use glob_prepro4

implicit none

logical :: dateidadec
integer :: imeas,itest,iunit,iscan,narg,next_free_unit
character(len=200) :: inputdatei,logdatei,logdatei_test
character(len=10) :: idchar
character(len=7) :: imeaschar
character(len=4) :: argchar

character(len=lengthcharmeas),dimension(:),allocatable :: measfile
logical,dimension(:),allocatable :: dualifg
integer,dimension(:),allocatable :: nptrfirstdir,nofblock,nifg &
  ,errflag,errflag_CO,icbfwd,icbbwd,icbfwd2,icbbwd2
integer,dimension(:,:),allocatable :: blocktype,blocklength,blockptr

real(8),dimension(:),allocatable :: JDdate
real,dimension(:),allocatable :: UTh,durationsec,astrelev,azimuth

character(len=6),dimension(:),allocatable :: YYMMDDlocal,HHMMSSlocal,YYMMDDUT

real,dimension(:),allocatable :: refspec,refspec2,sinc
real,dimension(:),allocatable :: cbfwd,cbbwd,cbfwd2,cbbwd2

! arrays for processing loop
real,dimension(:),allocatable :: ifgfwd,ifgbwd,ifgfwd2,ifgbwd2
real,dimension(:),allocatable :: specfwd,specbwd,specfwd2,specbwd2
real,dimension(:),allocatable :: specfwdrs,specbwdrs,specfwd2rs,specbwd2rs
real,dimension(:),allocatable :: specmeanrs,specmean2rs
complex,dimension(:),allocatable :: cspecfwd,cspecbwd,cspecfwd2,cspecbwd2

!====================================================================
!  read command argument
!  check presence of optional tccon.inp File
!  read input file
!====================================================================
call get_command_argument(1,inputdatei)

inquire (file = 'tccon.inp',exist = dateidadec)
if (dateidadec) then
    print *,'Optional TCCON input file detected...'
    iunit = next_free_unit()
    open (iunit,file = 'tccon.inp',status = 'old',action = 'read')
    call gonext(iunit,.false.)
    read (iunit,*) TCCONkind
    print *,'TCCONkind:',TCCONkind
    close (iunit)
else
   print *,'No optional TCCON input file detected...'
   TCCONkind = 0
end if

print *,'Reading input file...'
call read_input(trim(inputdatei))
print *,'Done!'
print *,'Number of raw measurements to be processed:',nmeas

if (nmeas .gt. maxmeas) then
    print *,'nmeas maxmeas: ',nmeas,maxmeas
    call warnout ('Too many files for processing!',0)
end if

!====================================================================
!  set ifg, spectral points and OPDmax according to choice of mpowFFT
!====================================================================
select case (mpowFFT)
    case (17)
        OPDmax = 1.8d0
        ifgradius = 56873
        maxspcrs = 56874            
    case (18)
        OPDmax = 3.0d0
        ifgradius = 94788
        maxspcrs = 94789
    case default
        call warnout("Invalid choice of mpowFFT (allowed: 17 or 18)!",0)
end select
maxifg = 2**mpowFFT
maxspc = maxifg / 2 

!====================================================================
!  allocation of general arrays, init sinc, read reference spectrum (for nue cal check)
!====================================================================
allocate (dualifg(nmeas))
allocate (measfile(nmeas),nptrfirstdir(nmeas),nofblock(nmeas) &
  ,nifg(nmeas),errflag(nmeas),errflag_CO(nmeas))
allocate (icbfwd(nmeas),icbbwd(nmeas),icbfwd2(nmeas),icbbwd2(nmeas))
allocate (cbfwd(nmeas),cbbwd(nmeas),cbfwd2(nmeas),cbbwd2(nmeas))
allocate (blocktype(maxblock,nmeas),blocklength(maxblock,nmeas),blockptr(maxblock,nmeas))
allocate (YYMMDDlocal(nmeas),HHMMSSlocal(nmeas),YYMMDDUT(nmeas))
allocate (JDdate(nmeas),UTh(nmeas),durationsec(nmeas),astrelev(nmeas),azimuth(nmeas))
nsinc = nzf * nconv
allocate (sinc(-nsinc:nsinc))
allocate (refspec(maxspc),refspec2(maxspc))

call prepare_sinc(sinc)

if (checkoutdec) then 
    call tofile_spec(trim(diagoutpath)//pathstr//'sinc.dat',2*nsinc+1,sinc(-nsinc:nsinc))
end if

call read_refspec('refspec.dat',maxspc,refspec)
call read_refspec('refspec2.dat',maxspc,refspec2)

!====================================================================
!  read file names
!====================================================================
print *,'Reading file names'
call read_meas_files(trim(inputdatei),nmeas,measfile)
print *,'Done!'

!====================================================================
!  read all OPUS file headers, ephemerid calculation
!====================================================================
errflag(1:nmeas) = 0
errflag_CO(1:nmeas) = 0

do imeas = 1,nmeas

    print *,'Read OPUS parms:',imeas

    ! read OPUS parms
    call read_opus_hdr(measfile(imeas),nptrfirstdir(imeas),nofblock(imeas))
    call read_opus_dir(measfile(imeas),nptrfirstdir(imeas),nofblock(imeas) &
      ,blocktype(1:maxblock,imeas),blocklength(1:maxblock,imeas) &
      ,blockptr(1:maxblock,imeas),dualifg(imeas),nifg(imeas))
    call read_opus_parms(imeas,measfile(imeas),nofblock(imeas) &
      ,blocktype(1:maxblock,imeas),blocklength(1:maxblock,imeas),blockptr(1:maxblock,imeas))

    ! check formal consistency of file with COCCON / preprocessor demands
    call checkOPUSparms(measfile(imeas),imeas)

end do

!====================================================================
!  Deallocation of general arrays
!====================================================================
deallocate (refspec,refspec2)
deallocate (sinc)

deallocate (JDdate,UTh,durationsec,astrelev,azimuth)
deallocate (YYMMDDlocal,HHMMSSlocal,YYMMDDUT)
deallocate (cbfwd,cbbwd,cbfwd2,cbbwd2)
deallocate (blocktype,blocklength,blockptr)
deallocate (measfile,nptrfirstdir,nofblock,nifg)
deallocate (errflag,errflag_CO,icbfwd,icbbwd,icbfwd2,icbbwd2)
deallocate (dualifg)

end program preprocess4









!====================================================================
!  checkOPUSparms
!====================================================================
subroutine checkOPUSparms(measfile,imeas)

use glob_prepro4, only : OPDmax
use glob_OPUSparms

implicit none

character(len=*),intent(in) :: measfile
integer,intent(in) :: imeas

if (OPUS_parms(imeas)%RES .lt. 0.8999999d0 / OPDmax) then
    print *,measfile
    print *,'OPUS RES:',OPUS_parms(imeas)%RES
    print *,'Requested RES:',0.9d0 / OPDmax
    call warnout ('RES too small!',0)
end if

if (modulo(OPUS_parms(imeas)%NSS,2) .gt. 0) then
    print *,measfile
    call warnout ('Uneven number of scans!',0)    
end if

if (scan(OPUS_parms(imeas)%AQM,"DD") .lt. 1) then
    print *,measfile
    call warnout ('IFG not double-sided!',0)
end if

end subroutine checkOPUSparms





!====================================================================
!  FFT
!====================================================================
subroutine FFT(ifg,spec)

use glob_prepro4,only : mpowFFT,maxifg,maxspc,pi

implicit none

real,dimension(maxifg),intent(in) :: ifg
complex,dimension(maxspc),intent(out) :: spec

integer :: i,j,k,l,n1,n2
real(8) :: angle,argument,xdum,ydum,c,s
real(8),dimension(:),allocatable :: x,y

allocate(x(maxifg),y(maxifg))

do i = 1,maxifg
    x(i) = real(ifg(i),8)
end do
y = 0.0d0

n2 = maxifg
do k = 1,mpowFFT
    n1 = n2
    n2 = n2 / 2
    angle = 0.0d0
    argument = 2.0d0 * pi / real(n1,8)
    do j = 0,n2 - 1
        c = cos(angle)
        s = sin(angle)
        do i = j,maxifg - 1,n1
            l = i + n2
            xdum = x(i+1) - x(l+1)
            x(i+1) = x(i+1) + x(l+1)
            ydum = y(i+1) - y(l+1)
            y(i+1) = y(i+1) + y(l+1)
            x(l+1) = xdum * c - ydum * s
            y(l+1) = ydum * c + xdum * s
        end do ! i loop
        angle = real(j + 1,8) * argument
    end do !j loop
end do !k loop

j = 0
do i = 0,maxifg - 2
    if (i .lt. j) then
        xdum = x(j+1)
        x(j+1) = x(i+1)
        x(i+1) = xdum
        ydum = y(j+1)
        y(j+1) = y(i+1)
        y(i+1) = ydum
    end if
    k = maxifg / 2
    do while (k .lt. j + 1)
        j = j - k
        k = k / 2
    end do
    j = j + k
end do ! i loop

do i = 1,maxspc
    spec(i) = cmplx(x(i),y(i))
end do

deallocate (x,y)

end subroutine FFT



!====================================================================
!  gonext: Einlesen bis zum naechsten $ Zeichen
!====================================================================
subroutine gonext(ifile,bindec)

implicit none

integer,intent(in) :: ifile
logical,intent(in) :: bindec

character(1) :: nextchar

nextchar='x'
do while (nextchar /= '$')
    if (bindec) then
        read(ifile) nextchar
    else
        read(ifile,'(A1)') nextchar
    end if
end do

end subroutine gonext



!====================================================================
!  mysinc
!====================================================================
real function mysinc(x)

implicit none

real,parameter :: spi = 3.141592654
real,parameter :: spihalb = 1.570796327

real,intent(in) :: x
real :: xabs,xabsmod,xabsqu,xabsmodqu


xabs = abs(x) + 1.0e-8
xabsqu = xabs * xabs
!xabsmod = mod(xabs,spi)

mysinc = sin(xabs) / (xabs + 5.0e-8 * xabsqu * xabsqu)

!if (xabsmod .ge. spihalb) xabsmod = spi - xabsmod
!
!xabsmodqu = xabsmod * xabsmod
!xabsqu = xabs * xabs
!mysinc = (xabsmod &
!  * (1.0 + xabsmodqu * (-0.1666595 + xabsmodqu &
!  * (0.008315 - xabsmodqu * 0.0001855)))) / (xabs + 2.0e-7 * xabsqu * xabsqu)

end function mysinc



!====================================================================
!  next_free_unit
!====================================================================
integer function next_free_unit()

implicit none

integer :: iu_free, istatus
logical :: is_open

iu_free = 9
is_open = .true.

do while (is_open .and. iu_free < 100)
    iu_free = iu_free+1
    inquire (unit=iu_free, opened=is_open, iostat=istatus)
    if (istatus .ne. 0) call warnout ('Error in inquiry!',0)
enddo

if (iu_free >= 100) call warnout ('No free unit < 100 found!',0)

next_free_unit = iu_free

end function next_free_unit



!====================================================================
!  OPUS_eval_char
!====================================================================
subroutine OPUS_eval_char(blocklength,binchar,charfilter,charwert)

use glob_prepro4,only : maxOPUSchar

implicit none

integer,intent(in) :: blocklength
character(len=blocklength),intent(in) :: binchar
character(len=3),intent(in) :: charfilter
character(len=maxOPUSchar),intent(out) :: charwert

integer(2) :: ityp,ireserved
integer :: ipos

ipos = index(binchar,charfilter//achar(0))
if (ipos .eq. 0) then
    call warnout('charfilter not found!',0)
end if

read(binchar(ipos+4:ipos+5),FMT='(A2)') ityp

read(binchar(ipos+6:ipos+7),FMT='(A2)') ireserved
    
if (ityp .ne. 2 .and. ityp .ne. 3) then
    call warnout('Inconsistent parameter kind in OPUS file!',0)
end if

charwert = '                                                  '
read(binchar(ipos+8:ipos+8+2*ireserved-1),FMT='(A)') charwert(1:2*ireserved)

end subroutine OPUS_eval_char



!====================================================================
!  OPUS_eval_int
!====================================================================
subroutine OPUS_eval_int(blocklength,binchar,charfilter,iwert)

implicit none

integer,intent(in) :: blocklength
character(len=blocklength),intent(in) :: binchar
character(len=3),intent(in) :: charfilter
integer,intent(out) :: iwert

integer(2) :: ityp,ireserved
integer :: ipos

ipos = index(binchar,charfilter//achar(0))
if (ipos .eq. 0) then
    call warnout('charfilter not found!',0)
end if

read(binchar(ipos+4:ipos+5),FMT='(A2)') ityp

read(binchar(ipos+6:ipos+7),FMT='(A2)') ireserved
    
if (ityp .ne. 0 .or. ireserved .ne. 2) then
    call warnout('Inconsistent parameter kind in OPUS file!',0)
end if

read(binchar(ipos+8:ipos+8+2*ireserved-1),FMT='(A4)') iwert

end subroutine OPUS_eval_int


!====================================================================
!  OPUS_eval_dble
!====================================================================
subroutine OPUS_eval_dble(blocklength,binchar,charfilter,dblewert)

implicit none

integer,intent(in) :: blocklength
character(len=blocklength),intent(in) :: binchar
character(len=3),intent(in) :: charfilter
real(8),intent(out) :: dblewert

integer(2) :: ityp,ireserved
integer :: ipos

ipos = index(binchar,charfilter//achar(0))
if (ipos .eq. 0) then
    call warnout('charfilter not found!',0)
end if

read(binchar(ipos+4:ipos+5),FMT='(A2)') ityp

read(binchar(ipos+6:ipos+7),FMT='(A2)') ireserved
    
if (ityp .ne. 1 .or. ireserved .ne. 4) then
    call warnout('Inconsistent parameter kind in OPUS file!',0)
end if

read(binchar(ipos+8:ipos+8+2*ireserved-1),FMT='(A8)') dblewert

end subroutine OPUS_eval_dble




!====================================================================
!  prepare_sinc
!====================================================================
subroutine prepare_sinc(sinc)

use glob_prepro4, only : nconv,nzf,nsinc,pi

implicit none

real,dimension(-nsinc:nsinc),intent(out) :: sinc

integer :: i
real(8) :: x,xapo,apowert

sinc(0) = 1.0
do i = 1,nsinc
    xapo = real(i,8) / real(nzf * (nconv - 2),8)
    if (xapo .gt. 1.0) then
        xapo = pi
    else
        xapo = pi * xapo
    end if
    apowert = 0.5d0 * (1.0d0 + cos(xapo))
    x = pi * real(i,8) / real(nzf,8)
    sinc(i) = apowert * sin(x) / x
    sinc(-i) = sinc(i)
end do

end subroutine prepare_sinc




!====================================================================
!  read_input: Einlesen der Eingabedatei
!====================================================================
subroutine read_input(inpdatei)

use glob_prepro4

implicit none

character(len=*),intent(in) :: inpdatei

character(len=300) :: zeile
logical :: marke,decfileda,decsize
integer :: iunit,iowert,imeas,next_free_unit,nfilebytes

iunit = next_free_unit()
open (iunit,file = trim(inpdatei),status = 'old',iostat = iowert)
if (iowert .ne. 0) then
    print *,trim(inpdatei)
    call warnout('Cannot open input file!',0)
end if

call gonext(iunit,.false.)
read(iunit,*) checkoutdec
read(iunit,*) mpowFFT
read(iunit,*) DCmin
read(iunit,*) DCvar

call gonext(iunit,.false.)
read(iunit,*) ILSapo,ILSphas
read(iunit,*) ILSapo2,ILSphas2

call gonext(iunit,.false.)
read(iunit,*) obsfixdec
read(iunit,*) obslocation
read(iunit,*) toffseth_UT
if (obsfixdec) then
    read(iunit,*) obsfixlatdeg,obsfixlondeg,obsfixaltkm
else
    continue
end if

call gonext(iunit,.false.)
read(iunit,'(L)') quietrundec
read(iunit,'(A)') diagoutpath
read(iunit,'(A)') binoutpath
if (diagoutpath .eq. 'standard') diagoutpath = 'diagnosis'

call gonext(iunit,.false.)
read(iunit,'(A)') infotext

call gonext(iunit,.false.)
! determine number of raw measurements to treat
marke = .false.
imeas = 0
do while (.not. marke)
    read(iunit,'(A)') zeile
    if (zeile(1:3) .eq. '***') then
        marke = .true.
    else        
        ! test file existence and size here
        inquire(file = zeile,exist = decfileda,size = nfilebytes)
        if (.not. decfileda) then
            print *,zeile
            call warnout('spectrum file does not exist!',0)
        end if
        if (nfilebytes .lt. minfilesize) then
            decsize = .false.
        else
            decsize = .true.
        end if
        if (decsize) imeas = imeas + 1
    end if
end do

close (iunit)
nmeas = imeas

end subroutine read_input



!====================================================================
!  read names of all files to be processed
!====================================================================
subroutine read_meas_files(inpdatei,nmeas,measfile)

use glob_prepro4, only : lengthcharmeas,minfilesize

implicit none

character(len=*),intent(in) :: inpdatei
integer,intent(in) :: nmeas
character(len=lengthcharmeas),dimension(nmeas),intent(out) :: measfile

logical :: marke,decfileda,decsize
character(len=lengthcharmeas) :: zeile
integer :: i,imeas,imeasall,iunit,iowert,next_free_unit,nfilebytes

iunit = next_free_unit()

open (iunit,file = trim(inpdatei),status = 'old',iostat = iowert)
if (iowert .ne. 0) then
    print *,trim(inpdatei)
    call warnout('Cannot open input file!',0)
end if

do i = 1,6
    call gonext(iunit,.false.)
end do

marke = .false.
imeas = 0
do while (.not. marke)
    read(iunit,'(A)') zeile
    if (zeile(1:3) .eq. '***') then
        marke = .true.
    else        
        ! test file size here
        inquire(file = zeile,exist = decfileda,size = nfilebytes)
        if (.not. decfileda) then
            print *,zeile
            call warnout('spectrum file does not exist!',0)
        end if
        if (nfilebytes .lt. minfilesize) then
            decsize = .false.
        else
            decsize = .true.
        end if
        if (decsize) then
            imeas = imeas + 1
            measfile(imeas) = trim(zeile)
            print *,trim(measfile(imeas))
        end if
    end if
end do

close (iunit)

end subroutine read_meas_files



!====================================================================
!  read_opus_dir
!====================================================================
subroutine read_opus_dir(measfile,nptrfirstdir,nofblock,blocktype &
  ,blocklength,blockptr,dualifg,nifg)

use glob_prepro4,only : maxblock,maxblength,maxifg

implicit none

character(len=*),intent(in) :: measfile
integer,intent(in) :: nptrfirstdir,nofblock
integer,dimension(maxblock),intent(out) :: blocktype,blocklength,blockptr
logical,intent(out) :: dualifg
integer,intent(out) :: nifg

character(len=1) :: charbyte
integer :: i,nifga,nifgb,iwert,magic,iunit,iowert,next_free_unit
real(8) :: progver

iunit = next_free_unit()

open (iunit,file = trim(measfile),form='unformatted',access ='stream',status = 'old',action = 'read',iostat = iowert)

do i = 1,nptrfirstdir
    read(iunit) charbyte
end do

do i = 1,nofblock
    read(iunit) iwert
    blocktype(i) = mod(iwert,2**16)
    read(iunit) blocklength(i)
    blocklength(i) = 4 * blocklength(i)
    read(iunit) blockptr(i)
end do

close (iunit)

nifga = 0
nifgb = 0
dualifg = .false.
do i = 1,nofblock
   if (blocktype(i) .eq. 2055) then
        nifga = blocklength(i)
    end if
    ! dual channel?
    if (blocktype(i) .eq. 34823) then
        dualifg = .true.
        nifgb = blocklength(i)
    end if
end do

if (nifga .eq. 0) then
    print *,measfile
    call warnout('Zero IFG block size!',0)
end if

if (dualifg .and. nifga .ne. nifgb) then
    print *,measfile
    call warnout('Differing sizes of dual channel IFGs!',0)
else
    if (mod(nifga,8) .ne. 0) then
        print*, measfile
        call warnout('Unexpected IFG size!',0)
    end if
    nifg = nifga / 8
end if

if (mod(nifg,2) .ne. 0) then
    print *,measfile
    call warnout('nifg not even!',0)
end if

if (nifg .gt. maxifg) then
    print *,measfile
    call warnout('IFG size too big!',0)
end if

end subroutine read_opus_dir



!====================================================================
!  read_opus_hdr
!====================================================================
subroutine read_opus_hdr(measfile,nptrfirstdir,nofblock)

use glob_prepro4, only : maxblock

implicit none

character(len=*),intent(in) :: measfile
integer,intent(out) :: nptrfirstdir,nofblock

character(len=1) :: charbyte
integer :: i,ntest,magic,iunit,iowert,next_free_unit
real(8) :: progver

iunit = next_free_unit()

open (iunit,file = trim(measfile),form='unformatted',access ='stream',status = 'old',action = 'read',iostat = iowert)
if (iowert .ne. 0) then
    print *,trim(measfile)
    call warnout('Cannot open measurement file!',0)
end if

read(iunit) magic
if (magic .ne. -16905718) then
    print *,'measurement file:',trim(measfile)
    call warnout('Not an OPUS file!',0)
end if

read(iunit) progver
!print *,progver

read(iunit) nptrfirstdir
!print *,nptrfirstdir

read(iunit) ntest ! Angabe maxblock
!print *,ntest

read(iunit) nofblock
!print *,nofblock
if (nofblock .gt. maxblock) then
    print *,'measurement file:',trim(measfile)
    call warnout('nofblock too big!',0)
end if

close (iunit)

end subroutine read_opus_hdr



!====================================================================
!  read OPUS parameters
!              
!====================================================================
subroutine read_opus_parms(imeas,measfile,nofblock,blocktype,blocklength,blockptr)

use glob_prepro4,only : maxblock,maxblength
use glob_OPUSparms

implicit none

character(len=*),intent(in) :: measfile
integer,intent(in) :: imeas,nofblock
integer,dimension(maxblock),intent(in) :: blocktype,blocklength,blockptr

integer :: i,iunit,iowert,next_free_unit
character(len=maxblength) :: binchar

! read variables from blocktype 32: HFL,LWN,GFW,GBW,TSC,SSM
do i = 1,nofblock
   if (blocktype(i) .eq. 32) exit
end do

iunit = next_free_unit()

open (iunit,file = trim(measfile),form='unformatted',access ='stream',status = 'old',action = 'read',iostat = iowert)
if (iowert .ne. 0) then
    print *,trim(measfile)
    call warnout('Cannot open measurement file!',0)
end if

if (blocklength(i) .gt. maxblength) then
    print *,trim(measfile)
    call warnout('Max blocklength exceeded!',0)
end if

read(unit = iunit,pos = blockptr(i) + 1) binchar(1:blocklength(i))
close (iunit)

call OPUS_eval_int(blocklength(i),binchar,'GFW',OPUS_parms(imeas)%GFW)
call OPUS_eval_int(blocklength(i),binchar,'GBW',OPUS_parms(imeas)%GBW)
call OPUS_eval_dble(blocklength(i),binchar,'HFL',OPUS_parms(imeas)%HFL)
call OPUS_eval_dble(blocklength(i),binchar,'LWN',OPUS_parms(imeas)%LWN)
call OPUS_eval_dble(blocklength(i),binchar,'TSC',OPUS_parms(imeas)%TSC)

! read variables from blocktype 48: NSS,AQM
do i = 1,nofblock
   if (blocktype(i) .eq. 48) exit
end do

iunit = next_free_unit()

open (iunit,file = trim(measfile),form='unformatted',access ='stream',status = 'old',action = 'read',iostat = iowert)
if (iowert .ne. 0) then
    print *,trim(measfile)
    call warnout('Cannot open measurement file!',0)
end if

if (blocklength(i) .gt. maxblength) then
    print *,trim(measfile)
    call warnout('Max blocklength exceeded!',0)
end if

read(unit = iunit,pos = blockptr(i) + 1) binchar(1:blocklength(i))
close (iunit)

!call OPUS_eval_char(blocklength,binchar,'VEL',OPUS_parms(imeas)%VEL)
!print*,OPUS_parms(imeas)%VEL

call OPUS_eval_int(blocklength(i),binchar,'NSS',OPUS_parms(imeas)%NSS)
call OPUS_eval_char(blocklength(i),binchar,'AQM',OPUS_parms(imeas)%AQM)
call OPUS_eval_dble(blocklength(i),binchar,'RES',OPUS_parms(imeas)%RES)

! read variables from blocktype 96: VEL,HPF,LPF
do i = 1,nofblock
   if (blocktype(i) .eq. 96) exit
end do

iunit = next_free_unit()

open (iunit,file = trim(measfile),form='unformatted',access ='stream',status = 'old',action = 'read',iostat = iowert)
if (iowert .ne. 0) then
    print *,trim(measfile)
    call warnout('Cannot open measurement file!',0)
end if

if (blocklength(i) .gt. maxblength) then
    print *,trim(measfile)
    call warnout('Max blocklength exceeded!',0)
end if

read(unit = iunit,pos = blockptr(i) + 1) binchar(1:blocklength(i))
close (iunit)

call OPUS_eval_char(blocklength(i),binchar,'VEL',OPUS_parms(imeas)%VEL)
call OPUS_eval_char(blocklength(i),binchar,'HPF',OPUS_parms(imeas)%HPF)
call OPUS_eval_char(blocklength(i),binchar,'LPF',OPUS_parms(imeas)%LPF)

! read variables from blocktype 2071: DAT,TIM

do i = 1,nofblock
   if (blocktype(i) .eq. 2071) exit
end do

iunit = next_free_unit()

open (iunit,file = trim(measfile),form='unformatted',access ='stream',status = 'old',action = 'read',iostat = iowert)
if (iowert .ne. 0) then
    print *,trim(measfile)
    call warnout('Cannot open measurement file!',0)
end if

if (blocklength(i) .gt. maxblength) then
    print *,trim(measfile)
    call warnout('Max blocklength exceeded!',0)
end if

read(unit = iunit,pos = blockptr(i) + 1) binchar(1:blocklength(i))
close (iunit)

call OPUS_eval_char(blocklength(i),binchar,'DAT',OPUS_parms(imeas)%DAT)
call OPUS_eval_char(blocklength(i),binchar,'TIM',OPUS_parms(imeas)%TIM)

end subroutine read_opus_parms



!====================================================================
!  read_refspec
!====================================================================
subroutine read_refspec(refspecfile,maxspc,refspec)

implicit none

character(len=*),intent(in) :: refspecfile
integer,intent(in) :: maxspc
real,dimension(maxspc),intent(out) :: refspec

integer :: i,icount,iunit,iowert,next_free_unit
real :: wert

iunit = next_free_unit()
! check availability of file, number of file entries
open (iunit,file = trim(refspecfile),status = 'old',iostat = iowert)
if (iowert .ne. 0) then
    print *,trim(refspecfile)
    call warnout('Cannot open refspec file!',0)
end if

icount = 0
do
    read(iunit,*,end = 102) wert
    icount = icount + 1
end do
102 continue
close (iunit)

if (icount .ne. maxspc) then
    print *,'maxspc:',maxspc
    print *,'icount:',icount
    call warnout('Incompatible # of entries in refspec!',0)
end if

iunit = next_free_unit()
open (iunit,file = trim(refspecfile),status = 'old',iostat = iowert)
do i = 1,icount
    read(iunit,*) refspec(i)
end do
close (iunit)

end subroutine read_refspec



!====================================================================
!  tofile_spec
!====================================================================
subroutine tofile_spec(ausdatei,nspec,spec)

implicit none

character(len=*),intent(in) :: ausdatei
integer,intent(in) :: nspec
real,dimension(nspec),intent(in) :: spec

integer :: i,iunit,next_free_unit

iunit = next_free_unit()

open (iunit,file = ausdatei,status = 'replace')

do i = 1,nspec
    write(iunit,'(ES13.6)') spec(i)
end do

close (iunit)

end subroutine tofile_spec



!====================================================================
!� Warnung rausschreiben und Programm evtl. beenden
!====================================================================
subroutine warnout(text,predec)

use ISO_FORTRAN_ENV, only : ERROR_UNIT
use glob_prepro4, only : quietrundec

implicit none

character(len=*),intent(in) :: text
integer,intent(in) :: predec
character(len=1) :: chardum
integer :: intdec

print *,'Warning:'
print *, trim(text)
if (predec .eq. 0) then
    if (.not. quietrundec) then
        print *,'This is a critical error, press return for terminating exection.'
        read *,chardum
        stop
    else
        print *,'This is a critical error. Quiet run option selected: End Programm'
        write (ERROR_UNIT, *) text
        call exit(1)
    end if
else
    if (.not. quietrundec) then
        print *,'Shutdown program: enter 0 / proceed with exection: enter 1:'
        read *, intdec
        if (intdec .eq. 0) stop
    else
        print *,'Quiet run option selected, continuing execution ...'
    end if
end if

end subroutine warnout

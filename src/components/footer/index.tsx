const Footer = () => {
  return (
    <div className="flex w-full mt-20 pt-5 px-6 pb-6 justify-center items-center shrink-0 border-t border-[#dad9d9] bg-white mx-auto">
      <div className="flex flex-col w-full h-42 shrink-0 text-[#929292] typo-body1-medium gap-2">
        <div>CRiT</div>
        <div>Creator in Trend</div>
        <br />
        <div>Copyright ⓒ CRiT. ALL Right Reserved</div>
        <div>
          문의:{' '}
          <a href="mailto:creatorintrend@gmail.com">
            <u>creatorintrend@gmail.com</u>
          </a>
        </div>
        <div>
          인스타그램:{' '}
          <a href="https://www.instagram.com/crit.for.you/">
            <u>@crit.for.you</u>
          </a>
        </div>
      </div>
    </div>
  );
};

export default Footer;

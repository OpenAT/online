base_phone_search
======================

Provides the method search_phone_fuzzy() for res.partner.
    
    This method will search the 'phone' and 'mobile' fields of res.partner for the given phone number.
    
    It will by default ignore all non digit characters and will search from right to left.
    e.g.: '+43 (0)660 1234 - 567 ' will be converted to '7654321066034'
    
    When we search for a phone number by self.env['res.partner'].search_phone_fuzzy('(0)660 12 34 567') we search for 
        1.) Search for partner where 'phone' or 'mobile' ends with '234567'
        2.) Use the phonenumbers Python Library to further narrow down the results
        3.) Return an record set with the found partner

Database search optimization
----------------------------

    # SELECT reverse(regexp_replace(regexp_replace('0043 (0) 3160 123-45-67 ', '[^0-9]', '', 'g'), '00*', ''))

    # CREATE OR REPLACE FUNCTION phone_clean_reverse(text) RETURNS text AS $$ 
    # SELECT concat(left(reverse(regexp_replace(regexp_replace($1, '[^0-9]', '', 'g'), '^000*', '')), 6));
    # $$ LANGUAGE 'sql' IMMUTABLE STRICT;
    # 
    # DROP INDEX idx_phone_reverse;
    # CREATE INDEX idx_phone_reverse ON res_partner(phone_clean_reverse(phone));
    # 
    # DROP INDEX idx_mobile_reverse;
    # CREATE INDEX idx_mobile_reverse ON res_partner(phone_clean_reverse(mobile));
    # 
    # select "id", firstname, lastname, phone 
    # from res_partner
    # where phone_clean_reverse(phone) = phone_clean_reverse('+43 (0) 7478-327');
    # 
    # select "id", firstname, lastname, mobile 
    # from res_partner
    # where phone_clean_reverse(mobile) = phone_clean_reverse('+43 (0) 7478-327');
    # 
    # select "id", firstname, lastname, phone, mobile 
    # from res_partner
    # where phone_clean_reverse(mobile) = phone_clean_reverse('+43 (0) 7478-327') 
    #       or phone_clean_reverse(phone) = phone_clean_reverse('+43 (0) 7478-327');

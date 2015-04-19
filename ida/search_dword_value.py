start = 0x8054
c = start
end = 0x982F

start = AskAddr(0x8000, "Enter start address.")
end = AskAddr(BeginEA(), "Enter string length.")
da_word = AskAddr(0xFFFFFFFF, "Enter string length.")

while c < end:
	dword = Dword(c)
	if dword == da_word:
		print "0x%08x --> 0x%08x"%(c, da_word)
		c +=4
		continue
	word = Word(c)
	if word + c == da_word:
		print "0x%08x --> 0x%08x"%(c+word, da_word)
		c +=2
		continue
	print word, dword, c
	c+=1

print "Finished searching for the strings.!"